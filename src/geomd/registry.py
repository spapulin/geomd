from .models import Node
from .parsers.json_parser import JsonParser
from .parsers.markdown_parser import MarkdownParser
from .parsers.geojson_parser import GeoJsonParser
from .parsers.geomarkdown_parser import GeoMarkdownParser
from .protocol import Parser, Renderer
from .renderers.geomarkdown_renderer import GeoMarkdownRenderer
from .renderers.json_renderer import JsonRenderer
from .renderers.markdown_renderer import MarkdownRenderer
from .renderers.geojson_renderer import GeoJsonRenderer


__all__ = [
    "convert", "parse", "render"
]

PARSERS: dict[str, Parser]  = {
    "json": JsonParser(),
    "md": MarkdownParser(),
    "geomd": GeoMarkdownParser(),
    "geojson": GeoJsonParser()
}


RENDERERS: dict[str, Renderer] = {
    "json": JsonRenderer(),
    "md": MarkdownRenderer(),
    "geojson": GeoJsonRenderer(),
    "geomd": GeoMarkdownRenderer()
}


def convert(text: str, src: str, dst: str) -> str:
    return render(parse(text, src), dst)


def parse(text: str, fmt: str) -> list[Node]:
    return PARSERS[fmt].parse(text)


def render(nodes: list[Node], fmt: str) -> str:
    return RENDERERS[fmt].render(nodes)