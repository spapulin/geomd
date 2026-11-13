from __future__ import annotations

import logging
from dataclasses import dataclass, field

import geojson

from ..constants import _EXTRA_FIELDS, _FIELD_MAPPING
from ..helpers import parse_metadata_from_html_comment
from ..models import (
    CodeBlock,
    Formatting,
    GeometryBlock,
    Heading,
    HtmlBlock,
    List,
    Node,
    Paragraph,
    Text,
    geometry_to_dict,
)
from .json_renderer import JsonRenderer

logger = logging.getLogger(__name__)


@dataclass
class _Section:
    """One heading with the content that belongs to it and its subsections."""

    heading: Heading | None
    content: list[Node] = field(default_factory=list)
    children: list[_Section] = field(default_factory=list)

    @property
    def title(self) -> str:
        if self.heading is None:
            return ""
        return _inline_text(self.heading.children)

    @property
    def level(self) -> int:
        return self.heading.level if self.heading is not None else 0


class GeoJsonRenderer(JsonRenderer):
    """Render document nodes to a GeoJSON FeatureCollection.

    Features are collected from the heading tree, not from the intermediate
    dict: whether a geometry block belongs to a feature or to a subsection of
    it depends on the heading level, and a dict keyed by heading text has lost
    that.  A section becomes a feature as soon as its own content or the
    content of one of its direct subsections holds a geometry block, which is
    what the specification says; ``field_mapping`` is not needed for it.
    """

    def render(self, nodes: list[Node], as_dict: bool = False) -> str | dict:
        root = _build_tree(nodes)
        roots = root.children

        if len(roots) == 1:
            title = roots[0].title
            features = self._features_of(roots[0])
        else:
            title = ""
            features = [feature for section in roots for feature in self._features_of(section)]

        feature_collection = geojson.FeatureCollection(features=features, title=title)
        if as_dict:
            return feature_collection
        return geojson.dumps(feature_collection)

    def _features_of(self, section: _Section) -> list[geojson.Feature]:
        geometry = _own_geometry(section)
        if geometry is None and section.level >= 2:
            # "A second-level heading becomes a Feature when one of its direct
            # subsections contains a geometry block."
            geometry = _subsection_geometry(section)
        if geometry is not None:
            return [self._feature(section, geometry)]

        features = [
            feature for child in section.children for feature in self._features_of(child)
        ]
        if not features and not section.children and section.content:
            logger.warning(
                "Section %r has no geometry block, so it is not a feature; its content is left out",
                section.title,
            )
        return features

    def _feature(self, section: _Section, geometry: GeometryBlock) -> geojson.Feature:
        title = section.title
        metadata_node = _metadata_node(section)
        metadata = parse_metadata_from_html_comment(metadata_node.raw) if metadata_node else {}
        field_mapping = metadata.get(_FIELD_MAPPING) or {}
        extra_names = list(metadata.get(_EXTRA_FIELDS) or {})
        owner = _geometry_owner(section)

        properties: dict = {}
        ignored_geometries: list[str] = []
        for child in section.children:
            if child.title in extra_names:
                properties[child.title] = self._value_of(child)
                continue
            if child is owner:
                continue
            if _own_geometry(child) is not None:
                ignored_geometries.append(child.title)
                continue
            properties[field_mapping.get(child.title, child.title)] = self._value_of(child)

        if ignored_geometries:
            logger.warning(
                "Feature %r holds more than one geometry; using the first and leaving out %s",
                title,
                ", ".join(repr(name) for name in ignored_geometries),
            )

        loose = [
            node for node in section.content
            if node is not metadata_node and not isinstance(node, (HtmlBlock, GeometryBlock))
        ]
        if loose:
            logger.warning(
                "Feature %r has content outside a subsection; it is not a property and is left out",
                title,
            )

        properties["title"] = title
        return geojson.Feature(
            geometry=geometry_to_dict(geometry.geometry),
            properties=properties,
            title=title,
        )

    def _value_of(self, section: _Section) -> object:
        geometry = _own_geometry(section)
        if geometry is not None:
            return geometry_to_dict(geometry.geometry)
        return self._render_section(section.content)


def _build_tree(nodes: list[Node]) -> _Section:
    root = _Section(heading=None)
    stack = [root]
    for node in nodes:
        if isinstance(node, Heading):
            while len(stack) > 1 and stack[-1].level >= node.level:
                stack.pop()
            section = _Section(heading=node)
            stack[-1].children.append(section)
            stack.append(section)
        else:
            stack[-1].content.append(node)
    return root


def _own_geometry(section: _Section) -> GeometryBlock | None:
    """The geometry block written directly under a heading."""
    return _first_geometry(section.content, section.title)


def _subsection_geometry(section: _Section) -> GeometryBlock | None:
    """The geometry block of the first direct subsection that has one."""
    for child in section.children:
        block = _first_geometry(child.content, child.title)
        if block is not None:
            return block
    return None


def _first_geometry(content: list[Node], title: str) -> GeometryBlock | None:
    blocks = [node for node in content if isinstance(node, GeometryBlock)]
    if len(blocks) > 1:
        logger.warning(
            "Section %r holds %d geometry blocks; using the first", title, len(blocks)
        )
    return blocks[0] if blocks else None


def _geometry_owner(section: _Section) -> _Section | None:
    """The section holding the feature's geometry: itself or a direct subsection."""
    if _own_geometry(section) is not None:
        return section
    for child in section.children:
        if _own_geometry(child) is not None:
            return child
    return None


def _geometry_of(section: _Section) -> GeometryBlock | None:
    owner = _geometry_owner(section)
    if owner is None:
        return None
    return _own_geometry(owner)


def _metadata_node(section: _Section) -> HtmlBlock | None:
    for node in section.content:
        if isinstance(node, HtmlBlock) and node.raw.lstrip().startswith("<!--"):
            return node
    return None


def _inline_text(nodes: list[Node]) -> str:
    parts: list[str] = []
    for node in nodes:
        if isinstance(node, Text):
            parts.append(node.raw)
        elif isinstance(node, (Formatting, Paragraph, List, CodeBlock)):
            parts.append(_inline_text(node.children))
    return "".join(parts)

