from __future__ import annotations

from typing import Literal

from mistune import create_markdown

from .errors import UnknownFormatError
from .models import Node
from .parsers.geojson_parser import GeoJsonParser
from .parsers.geomarkdown_parser import GeoMarkdownParser
from .parsers.json_parser import JsonParser
from .parsers.markdown_parser import MarkdownParser
from .protocol import Parser, Renderer
from .renderers.geojson_renderer import GeoJsonRenderer
from .renderers.geomarkdown_renderer import GeoMarkdownRenderer
from .renderers.html_renderer import GeoHTMLRenderer
from .renderers.json_renderer import JsonRenderer
from .renderers.markdown_renderer import MarkdownRenderer

__all__ = [
    "convert", "parse", "render", "PARSERS", "RENDERERS", "SOURCE_FORMATS", "DESTINATION_FORMATS"
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

SOURCE_FORMATS: tuple[str, ...] = tuple(PARSERS)
DESTINATION_FORMATS: tuple[str, ...] = tuple(RENDERERS)


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

    Raises :class:`geomd.errors.GeoMdError` (a ``ValueError``) when the input
    cannot be read as `src` or a geometry block is not a GeoJSON geometry.
    """

    parser = _require(src, PARSERS, "source")
    if dst == "html":
        markdown = create_markdown(renderer=GeoHTMLRenderer())
        if src in {"md", "geomd"}:
            return markdown(text)
        md_str = render(parser.parse(text), "geomd")
        return markdown(md_str)
    renderer = _require(dst, RENDERERS, "destination")
    return renderer.render(parser.parse(text), as_dict=as_dict)


def parse(text: str, fmt: SrcFormat) -> list[Node]:
    """Parse `text` into document nodes."""
    return _require(fmt, PARSERS, "source").parse(text)


def render(
        nodes: list[Node],
        fmt: DstFormat,
        as_dict: bool = False
) -> str | dict:
    """Render document nodes as `fmt`."""
    return _require(fmt, RENDERERS, "destination").render(nodes, as_dict=as_dict)


def _require(fmt: str, table: dict, kind: str) -> Parser | Renderer:
    try:
        return table[fmt]
    except KeyError:
        raise UnknownFormatError(fmt, list(table)) from None
