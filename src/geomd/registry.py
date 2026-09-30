from typing import Literal

from .models import Node
from .parsers.json_parser import JsonParser
from .parsers.markdown_parser import MarkdownParser
from .parsers.geojson_parser import GeoJsonParser
from .parsers.geomarkdown_parser import GeoMarkdownParser
from .protocol import Parser, Renderer
from .renderers.geomarkdown_renderer import GeoMarkdownRenderer
from .renderers.html_renderer import GeoHTMLRenderer
from .renderers.json_renderer import JsonRenderer
from .renderers.markdown_renderer import MarkdownRenderer
from .renderers.geojson_renderer import GeoJsonRenderer

from mistune import create_markdown


__all__ = [
    "convert", "parse", "render"
]

SrcFormat = Literal["json", "md", "geomd", "geojson"]
DstFormat = Literal["json", "md", "geomd", "geojson", "html"]

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
    "geomd": GeoMarkdownRenderer(),
    "html": GeoHTMLRenderer()
}


def convert(
        text: str,
        src: SrcFormat,
        dst: DstFormat,
        as_dict: bool = False
) -> str | dict:
    """
    Convert text from `src` format to `dst` format.

    HTML output is rendered with mistune; JSON/GeoJSON is first
    converted to Markdown/GeoMarkdown via geomd, then rendered
    to HTML. All other destinations are produced via geomd.
    """

    if dst == "html":
        markdown = create_markdown(renderer=GeoHTMLRenderer())
        if src in {"md", "geomd"}:
            return markdown(text)
        md_str = render(parse(text, src), "geomd")
        return markdown(md_str)
    return render(parse(text, src), dst, as_dict=as_dict)


def parse(text: str, fmt: SrcFormat) -> list[Node]:
    return PARSERS[fmt].parse(text)


def render(
        nodes: list[Node],
        fmt: DstFormat,
        as_dict: bool = False
) -> str:
    return RENDERERS[fmt].render(nodes, as_dict=as_dict)