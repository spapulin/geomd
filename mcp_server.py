from fastmcp import FastMCP
import geomd as gmd
from geomd.registry import SrcFormat, DstFormat

mcp = FastMCP("geomd-mcp")


@mcp.tool
def convert_to_geomd(geojson_text: str) -> str:
    """Convert the GeoJSON document to GeoMarkdown."""
    return _convert(data=geojson_text, src="geojson", dst="geomd")


@mcp.tool
def convert_to_geojson(geomd_text: str) -> str:
    """Convert the GeoMarkdown document to GeoJSON."""
    return _convert(data=geomd_text, src="geomd", dst="geojson")


def _convert(data: str, src: SrcFormat, dst: DstFormat) -> str:
    return gmd.convert(
        text=data,
        src=src,
        dst=dst
    )


if __name__ == "__main__":
    mcp.run()
