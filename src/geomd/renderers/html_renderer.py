import logging
import uuid
from json import JSONDecodeError
from typing import Any, Iterable
from xml.etree import ElementTree

from mistune import HTMLRenderer, Markdown, BlockState
import geojson

from .markdown_renderer import to_link_anchor, heading_to_text
from .. import GeometryBlock, HtmlBlock
from ..models import Node, Heading, Paragraph, TextBlock, Text, Image, InlineFormat, CodeBlock, List, ListItem, Link

logger = logging.getLogger(__name__)


class GeoHTMLRenderer:

    def __init__(self):
        self._md = Markdown(renderer=GeoHTMLRenderer._Renderer())

    def render(
            self,
            nodes: list[Node],
            *,
            as_dict: bool = False,
            auto_contents: bool = False,
            contents_title: str = "Contents"
    ) -> str:
        if as_dict:
            raise NotImplementedError(
                f"{type(self).__name__} does not support as_dict=True; it renders text only"
            )
        return self._to_html(nodes, auto_contents, contents_title)

    def _to_html(self, nodes: list[Node], auto_contents: bool, contents_title: str) -> str:
        tokens = self._convert_to_tokens(nodes, auto_contents, contents_title)
        if not tokens: return ""
        state = BlockState()
        state.tokens = tokens
        return self._md.render_state(state)

    def _convert_to_tokens(self, nodes: list[Node], auto_contents: bool, contents_title: str):

        tokens = []
        contents_items: list = []
        contents_start: int = -1

        for i, node in enumerate(nodes):
            token = self._convert_to_token(node)
            if token is not None:
                if auto_contents and isinstance(node, Heading) and node.level == 2:
                    if contents_start == -1:
                        contents_start = i
                    heading_text = heading_to_text(node)
                    link_anchor = to_link_anchor(heading_text)
                    # Assign id that will be used as html tag id
                    token["attrs"]["id"] = link_anchor
                    # Compose contents items as list_item type
                    contents_items.append({
                        "type": "list_item",
                        "children": [{
                            "type": "block_text",
                            "children": [{
                                "type": "link",
                                "children": [{"type": "text", "raw": heading_text}],
                                "attrs": {"url": "#" + link_anchor}}
                            ],
                        }]
                    })

                tokens.append(token)

        if auto_contents and contents_start != -1:
            tokens.insert(contents_start, {
                "type": "heading",
                "text": contents_title,
                "attrs": {"level": 3}
            })
            tokens.insert(contents_start + 1, {
                "type": "list",
                "children": contents_items,
                "tight": True,
                "bullet": "-",
                "attrs": {"depth": 0, "ordered": False}
            })

        return tokens

    def _convert_to_token(self, node: Node):
        match node:
            case Heading():
                return self._convert_heading(node)
            case Paragraph():
                return self._convert_paragraph(node)
            case TextBlock():
                return self._convert_text_block(node)
            case Text():
                return self._convert_text(node)
            case Image():
                return self._convert_image(node)
            case Link():
                return self._convert_link(node)
            case InlineFormat():
                return self._convert_inline_format(node)
            case CodeBlock():
                return self._convert_code_block(node)
            case GeometryBlock():
                return self._convert_geometry_block(node)
            case List():
                return self._convert_list(node)
            case ListItem():
                return self._convert_list_item(node)
            case HtmlBlock():
                return self._convert_html_block(node)
            case _:
                logger.error(f"Unhandled node: {node}")
                return None

    def _convert_heading(self, node: Heading):
        return {
            'type': 'heading',
            'attrs': {'level': node.level},
            'style': 'atx',
            'children': [token for child in node.children if (token := self._convert_to_token(child))]
        }

    def _convert_paragraph(self, node: Paragraph):
        return {
            'type': 'paragraph',
            'children': [token for child in node.children if (token := self._convert_to_token(child))]
        }

    def _convert_text_block(self, node: TextBlock):
        return {
            'type': 'block_text',
            'children': [token for child in node.children if (token := self._convert_to_token(child))]
        }

    def _convert_image(self, node: Image):
        return {
            'type': 'image',
            'children': [{'type': 'text', 'raw': node.title}],
            'attrs': {'url': node.url, 'title': " | ".join([node.title, node.alt])}
        }

    def _convert_link(self, node: Link):
        return {
            'type': 'link',
            'children': [{'type': 'text', 'raw': node.title}],
            'attrs': {'url': node.url}
        }

    def _convert_text(self, node: Text):
        return {'type': 'text', 'raw': node.raw}

    def _convert_inline_format(self, node: InlineFormat):
        token_type = "strong"
        if node.kind == "*":
            token_type = "emphasis"
        return {
            'type': token_type,
            'children': [token for child in node.children if (token := self._convert_to_token(child))]
        }

    def _convert_code_block(self, node: CodeBlock):
        return {
            'type': 'block_code',
            'raw': node.raw,
            'style': 'fenced',
            'marker': '```',
            'attrs': {'info': node.language}
        }

    def _convert_geometry_block(self, node: GeometryBlock):
        return {
            'type': 'geometry',
            'raw': geojson.dumps(node.geometry)
        }

    def _convert_list(self, node: List):
        return {
            'type': 'list',
            'children': [token for child in node.children if (token := self._convert_to_token(child))],
            'tight': True,
            'bullet': '-',
            'attrs': {'depth': 0, 'ordered': node.ordered}
        }

    def _convert_list_item(self, node: ListItem):
        return {
            'type': 'list_item',
            'children': [token for child in node.children if (token := self._convert_to_token(child))]
        }

    def _convert_html_block(self, node: HtmlBlock):
        return {
            'type': 'block_html',
            'raw': node.raw
        }

    class _Renderer(HTMLRenderer):

        HTML_TEMPLATE = """\
        <!doctype html>
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

        def __init__(self):
            super().__init__()
            self.register("geometry", self.geometry_block)

        def __call__(self, tokens, state):
            body = super().__call__(tokens, state)
            return self.HTML_TEMPLATE.format(body=body)

        def block_html(self, raw: str):
            if not raw.startswith("<!--"):
                return super().block_html(raw)
            return raw

        def geometry_block(self, renderer, raw: str) -> str:

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
                    var data = {raw};
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
