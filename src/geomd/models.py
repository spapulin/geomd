from __future__ import annotations

from dataclasses import dataclass, field
from typing import ClassVar

import geojson


def geometry_to_dict(geometry: object) -> dict | None:
    """Return a plain dict for a GeoJSON object, or ``None`` for a null geometry."""
    if geometry is None:
        return None
    interface = getattr(geometry, "__geo_interface__", None)
    if interface is not None:
        return dict(interface)
    if isinstance(geometry, dict):
        return geometry
    raise TypeError(f"not a GeoJSON geometry: {geometry!r}")


@dataclass
class Node:

    children: list[Node] = field(default_factory=list)

    NODE_TYPE: ClassVar[str] = ""

    def to_dict(self) -> dict:
        result = {"type": self.NODE_TYPE}
        for attr, val in self.__dict__.items():
            if attr == "children":
                if val:
                    result["children"] = [node.to_dict() for node in val]
            elif val not in (None, ""):
                result[attr] = val
        return result


@dataclass
class Heading(Node):
    NODE_TYPE = "heading"
    level: int = 1


@dataclass
class Paragraph(Node):
    NODE_TYPE = "paragraph"


@dataclass
class Text(Node):
    NODE_TYPE = "text"
    raw: str = ""


@dataclass
class Link(Node):
    NODE_TYPE = "link"
    url: str = ""
    title: str = ""


@dataclass
class Image(Node):
    NODE_TYPE = "image"
    url: str = ""
    alt: str = ""
    title: str = ""


@dataclass
class Formatting(Node):
    """Inline emphasis, strong emphasis or strikethrough.

    ``markup`` keeps the source markers (``*``, ``**``, ``~~``) so a Markdown
    round trip can put them back; text-only renderers drop them.
    """

    NODE_TYPE = "formatting"
    markup: str = ""


@dataclass
class CodeBlock(Node):
    NODE_TYPE = "code_block"
    raw: str = ""
    language: str = ""


@dataclass
class List(Node):
    NODE_TYPE = "list"
    ordered: bool = False
    start: int = 1
    depth: int = 0


@dataclass
class ListItem(Node):
    NODE_TYPE = "list_item"


@dataclass
class HtmlBlock(Node):
    NODE_TYPE = "html_block"
    raw: str = ""


@dataclass
class GeometryBlock(Node):
    """A ``geometry`` fenced block.

    ``raw`` keeps the original body so a document with a broken block can be
    written back unchanged instead of being silently replaced by ``null``;
    ``error`` records why the body could not be read as GeoJSON.
    """

    NODE_TYPE = "geometry_block"
    geometry: geojson.GeoJSON | None = None
    raw: str = ""
    error: str | None = None

    @property
    def is_valid(self) -> bool:
        return self.error is None

    def to_dict(self) -> dict:
        result: dict = {"type": self.NODE_TYPE, "geometry": geometry_to_dict(self.geometry)}
        if self.raw:
            result["raw"] = self.raw
        if self.error:
            result["error"] = self.error
        return result
