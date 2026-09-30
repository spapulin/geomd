import geojson

from .json_renderer import JsonRenderer
from ..models import Node, List, Paragraph, GeometryBlock, HtmlBlock


class GeoJsonRenderer(JsonRenderer):
    """Render document nodes to a GeoJSON FeatureCollection string."""

    def render(self, nodes: list[Node], as_dict: bool = False) -> str | dict:
        json_dict = super()._render_json(nodes)
        formatted_dict = self._map_fields_and_add_extra_fields(json_dict)
        features, extra = self._build_features(formatted_dict)
        feature_collection = geojson.FeatureCollection(features=features, **extra)
        if as_dict:
            return feature_collection
        return geojson.dumps(feature_collection)

    def _build_features(
            self,
            data: dict,
            title: str | None = None
    ) -> tuple[list[geojson.Feature], dict]:
        """Recursively split data into Features (dicts with geometry) and extra properties."""

        # TODO: Now we must define a geometry field in field_mapping of
        #   markdown file. Perhaps it's better to automatically assign
        #   "geometry" to field with GeometryBlock value within section
        # A dict containing "geometry" becomes one Feature,
        # everything else bubbles up
        if "geometry" in data:
            geometry = data.pop("geometry")
            # TODO: Include to _metadata default name for title or
            #   disable it at all
            # Note: We assign header value to _title as default property name,
            # and include it in feature properties
            data["title"] = title
            # Note: Header name we assign to extra field of Feature
            return [geojson.Feature(
                geometry=geometry,
                properties=data,
                title=title
            )], {}

        extra: dict = {}
        features: list[geojson.Feature] = list()

        # FIXME: We add title here to preserve top level
        #   header in title property
        extra["title"] = title

        for key, value in data.items():
            if isinstance(value, dict):
                feats, ext = self._build_features(
                    data=value,
                    title=key
                )
                features.extend(feats)
                extra.update(ext)
            else:
                extra[key] = value

        return features, extra

    def _render_section(self, nodes: list[Node]) -> list | dict | str:
        """Render a section of nodes."""

        # Fast path: a single List/GeometryBlock/HtmlBlock maps to a non-paragraph value
        if len(nodes) == 1:
            node = nodes[0]
            if isinstance(node, List):
                return self._render_list_block(nodes[0].children)
            elif isinstance(node, GeometryBlock):
                return node.geometry
            elif isinstance(node, HtmlBlock):
                return node.raw

        # General path: render each supported node to a string, join with blank lines
        result: list[str] = list()
        for node in nodes:
            if isinstance(node, List):
                result.append(self._render_inline_list(node.children, ordered=node.ordered))
            elif isinstance(node, Paragraph):
                result.append(self._render_paragraph(node.children))
        return "\n\n".join(result)