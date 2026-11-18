import uuid
from json import JSONDecodeError
from typing import Any, Iterable
from xml.etree import ElementTree

from mistune import HTMLRenderer, Markdown, BlockState
import geojson

from .markdown_renderer import to_link_anchor


class GeoHTMLRenderer(HTMLRenderer):

    HTML_TEMPLATE = """<!doctype html>
    <html>
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ margin: 0; font-family: system-ui, sans-serif; }}
        .md-content {{ max-width: 800px; margin: 0 auto; padding: 16px; overflow-wrap: anywhere; }}
        ul.image-list {{ display: inline-flex; flex-wrap: wrap; list-style: none; padding: 0; margin: 0; gap: 10px; }}
        ul.image-list li {{ list-style: none; }}
        ul.image-list img {{ height: 100px; width: auto; display: block; }}
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

    def list(self, text: str, ordered: bool, **attrs: Any) -> str:
        # TODO: Create ImageList document node instead
        root = ElementTree.fromstring(f'<ul class="image-list">{text.strip()}</ul>')
        items = root.findall("li")
        if items:
            for li in items:
                img = li.find("img")
                if img is None:
                    break
                link = ElementTree.Element(
                    "a",
                    attrib={
                        "href": img.get("src", ""),
                        "target": "_blank",
                        "rel": "noopener noreferrer",
                    }
                )
                li.remove(img)
                link.append(img)
                li.append(link)
            else:
                return ElementTree.tostring(root, encoding="unicode")

        return super().list(text, ordered, **attrs)

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


class ContentsInjectorPlugin:
    """Mistune plugin that injects an auto-generated table of contents."""

    def __init__(self, only_heading_ids: bool = False, contents_title: str = "Contents"):
        self.contents_title = contents_title
        self.only_heading_ids = only_heading_ids

    def __call__(self, md: Markdown) -> None:
        # Register the instance method as a before_render_hook
        md.before_render_hooks.append(self.add_contents_token_hook)

    def add_contents_token_hook(self, md: Markdown, state: BlockState):
        if self.only_heading_ids:
            tokens = self._add_heading_id(state)
        else:
            contents_tokens = self._create_contents_tokens(state)
            tokens = list(self._tokens_with_contents(state.tokens, contents_tokens))

        state.tokens = tokens

    def _add_heading_id(self, state) -> list[dict[str, Any]]:
        tokens = state.tokens
        for token in tokens:
            # We use only level 2 heading as contents item
            if (token.get("type") == "heading" and token.get("attrs") or {}).get("level") == 2:
                heading = token.get("text")
                link_anchor = to_link_anchor(heading)
                # Assign id that will be used as html tag id
                token["attrs"]["id"] = link_anchor
        return tokens

    def _create_contents_tokens(self, state):
        """Contents tokens = contents title + contents items."""

        contents_tokens = []
        contents_items = []
        tokens = state.tokens
        for token in tokens:
            # We use only level 2 heading as contents item
            if (token.get("type") == "heading" and token.get("attrs") or {}).get("level") == 2:
                heading = token.get("text")
                link_anchor = to_link_anchor(heading)
                # Assign id that will be used as html tag id
                token["attrs"]["id"] = link_anchor
                # Compose contents items as list_item type
                contents_items.append({
                    "type": "list_item",
                    "children": [{
                        "type": "block_text",
                        "children": [{
                            "type": "link",
                            "children": [{"type": "text", "raw": heading}],
                            "attrs": {"url": "#" + link_anchor}}
                        ],
                    }]
                })

        if contents_items:
            contents_tokens.append({
                "type": "heading",
                "text": self.contents_title,
                "attrs": {"level": 3}
            })
            contents_tokens.append({
                "type": "list",
                "children": contents_items,
                "tight": True,
                "bullet": "-",
                "attrs": {"depth": 0, "ordered": False}
            })

        return contents_tokens

    def _tokens_with_contents(self, tokens, contents_tokens) -> Iterable[dict[str, Any]]:
        contents_injected = False
        for token in tokens:
            if not contents_injected and token.get("type") == "heading" and  (token.get("attrs") or {}).get("level") == 2:
                for contents_token in contents_tokens:
                    yield contents_token
                contents_injected = True
            yield token
