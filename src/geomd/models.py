from dataclasses import dataclass, field
from typing import ClassVar

import geojson


@dataclass
class Node:

    children: list["Node"] = field(default_factory=list)

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
class CodeBlock(Node):
    NODE_TYPE = "code_block"
    raw: str = ""
    language: str = ""


@dataclass
class List(Node):
    NODE_TYPE = "list"
    ordered: bool = False
    start: int = 1


@dataclass
class ListItem(Node):
    NODE_TYPE = "list_item"


@dataclass
class HtmlBlock(Node):
    NODE_TYPE = "html_block"
    raw: str = ""


@dataclass
class GeometryBlock(Node):
    NODE_TYPE = "geometry_block"
    geometry: geojson.GeoJSON | None = None


# def from_dict(d: dict) -> Node:
#
#     node_type: str = d["type"]
#     children = [from_dict(c) for c in d.get("children", [])]
#     attrs = {attr: v for attr, v in d.items() if attr not in ("type", "children")}
#
#     if node_type == Heading.NODE_TYPE:
#         return Heading(children=children, **attrs)
#     elif node_type == Paragraph.NODE_TYPE:
#         return Paragraph(children=children)
#     elif node_type == Text.NODE_TYPE:
#         return Text(children=children, **attrs)
#     else:
#         raise ValueError(f"unknown node type: {node_type}")
