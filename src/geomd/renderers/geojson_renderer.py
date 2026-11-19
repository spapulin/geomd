import geojson

from .json_renderer import JsonRenderer
from ..models import Node, List, Paragraph, GeometryBlock, HtmlBlock


class GeoJsonRenderer(JsonRenderer):
    """Render document nodes to a GeoJSON FeatureCollection string."""

    def render(
            self,
            nodes: list[Node],
            *,
            as_dict: bool = False,
            auto_contents: bool = False,
            contents_title: str = "Contents"
    ) -> str | dict:
        if auto_contents:
            raise NotImplementedError(
                f"{type(self).__name__} does not support auto_contents=True"
            )

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

        # A dict containing "geometry" becomes one Feature,
        # everything else bubbles up
        if "geometry" in data:
            return self._build_feature(data, "geometry", title)

        # If the "geometry" property is not defined, search through
        # the data items for a dict whose "language" field equals
        # "geometry"
        for key, value in data.items():
            if isinstance(value, dict):
                if value.get("language") == "geometry":
                    return self._build_feature(data, key, title)

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

    def _build_feature(self, data, key, title):
        geometry_block = data.pop(key)
        # TODO: Include to _metadata default name for title or
        #   disable it at all
        # Note: We assign header value to "title" as default property name,
        # and include it in feature properties
        data["title"] = title
        # Note: Header name we assign to extra field of Feature
        return [geojson.Feature(
            geometry=geometry_block["code"],
            properties=data,
            title=title
        )], {}

    def _render_geometry_block(self, node: GeometryBlock) -> dict:
        return {
            "language": "geometry",
            "code": node.geometry
        }