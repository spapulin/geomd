from __future__ import annotations

import logging
import uuid

import geojson
import mistune

from ..errors import InvalidGeometryError
from ..geometry import loads_geometry

logger = logging.getLogger(__name__)


class GeoHTMLRenderer(mistune.HTMLRenderer):
    """Markdown to HTML, drawing every ```geometry block on a Leaflet map."""

    HTML_TEMPLATE = """<!doctype html>
        <html lang="en">
        <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {{ margin: 0; font-family: system-ui, sans-serif; }}
            .md-content {{ max-width: 800px; margin: 0 auto; padding: 16px; overflow-wrap: anywhere; }}
        </style>
        <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
        <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
        </head>
        <body>
            <div class="md-content">{body}</div>
        </body>
        </html>"""

    def __call__(self, tokens, state):
        body = super().__call__(tokens, state)
        return self.HTML_TEMPLATE.format(body=body)

    def block_html(self, html: str):
        if not html.startswith("<!--"):
            return super().block_html(html)
        return html

    def block_code(self, code, info=None):

        language = info.strip() if info else ""
        if language != "geometry":
            return super().block_code(code, info)

        try:
            geometry = loads_geometry(code)
        except InvalidGeometryError as exc:
            logger.warning("Drawing an invalid geometry block as plain code: %s", exc)
            return super().block_code(code, info)

        if geometry is None:
            # A null geometry has nothing to draw.
            return super().block_code(code, info)

        safe_geojson_str = _script_safe(geometry)

        # Unique id for each map on one page
        map_id = f"geo-map-{uuid.uuid4().hex}"

        return f'''
            <div id="{map_id}" class="geo-map" style="height:400px;width:100%"></div>
            <script>
            (function() {{
                var customIcon = L.icon({{
                    iconUrl:       'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
                    iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
                    shadowUrl:     'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
                    iconSize:    [25, 41],
                    iconAnchor:  [12, 41],
                    popupAnchor: [1, -34],
                    shadowSize:  [41, 41]
                }});
                var data = {safe_geojson_str};
                var map = L.map("{map_id}");
                L.tileLayer("https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png", {{
                    attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                }}).addTo(map);
                var layer = L.geoJSON(data, {{
                        pointToLayer: function (feature, latlng) {{
                            return L.marker(latlng, {{ icon: customIcon }});
                        }}
                }}).addTo(map);
                map.fitBounds(layer.getBounds());
            }})();
            </script>  
        '''


def _script_safe(geometry) -> str:
    """Serialise a geometry for a ``<script>`` body.

    ``<`` is escaped so a string in the geometry cannot close the script
    element, which would make a malformed block run as page JavaScript.
    """
    return geojson.dumps(geometry).replace("<", "\\u003c")
