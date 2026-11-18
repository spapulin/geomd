from typing import Literal

from .models import Node
from .parsers.json_parser import JsonParser
from .parsers.markdown_parser import MarkdownParser
from .parsers.geojson_parser import GeoJsonParser
from .parsers.geomarkdown_parser import GeoMarkdownParser
from .protocol import Parser, Renderer
from .renderers.geomarkdown_renderer import GeoMarkdownRenderer
from .renderers.html_renderer import GeoHTMLRenderer, ContentsInjectorPlugin
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
        *,
        as_dict: bool = False,
        auto_contents: bool = False,
        contents_title: str = "Contents"
) -> str | dict:
    """
    Convert text from `src` format to `dst` format.

    HTML output is rendered with mistune; JSON/GeoJSON is first
    converted to Markdown/GeoMarkdown via geomd, then rendered
    to HTML. All other destinations are produced via geomd.
    """

    if dst == "html":
        if src in {"md", "geomd"}:
            plugins = [ContentsInjectorPlugin()] if auto_contents else None
            md_str = text
        else:
            plugins = [ContentsInjectorPlugin(only_heading_ids=True)] if auto_contents else None
            md_str = render(
                parse(text, src),
                fmt="geomd",
                auto_contents=auto_contents,
                contents_title=contents_title
            )
        return create_markdown(renderer=GeoHTMLRenderer(), plugins=plugins)(md_str)

    return render(
        parse(text, src),
        dst,
        as_dict=as_dict,
        auto_contents=auto_contents,
        contents_title=contents_title
    )


def parse(text: str, fmt: SrcFormat) -> list[Node]:
    return PARSERS[fmt].parse(text)


def render(
        nodes: list[Node],
        fmt: DstFormat,
        *,
        as_dict: bool = False,
        auto_contents: bool = False,
        contents_title: str = "Contents"
) -> str:
    return RENDERERS[fmt].render(
        nodes,
        as_dict=as_dict,
        auto_contents=auto_contents,
        contents_title=contents_title
    )