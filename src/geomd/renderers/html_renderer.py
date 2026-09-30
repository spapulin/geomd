import uuid
from json import JSONDecodeError

import mistune
import geojson

class GeoHTMLRenderer(mistune.HTMLRenderer):

    HTML_TEMPLATE = """<!doctype html>
        <html lang="ru">
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

        language = info.strip() if info else ''
        if language != "geometry":
            return super().block_code(code, info)

        geojson_str = code.strip()
        try:
            geojson_data = geojson.loads(geojson_str)
        except JSONDecodeError as e:
            return super().block_code(code, info)

        safe_geojson_str = geojson.dumps(geojson_data)

        # Unique id for each map on one page
        map_id = f'geo-map-{uuid.uuid4()}'

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
