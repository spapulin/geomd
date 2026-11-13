import logging

from .errors import (
    DroppedContentWarning,
    GeoMdError,
    InvalidDocumentError,
    InvalidGeometryError,
    UnknownFormatError,
)
from .models import (
    CodeBlock,
    Formatting,
    GeometryBlock,
    Heading,
    HtmlBlock,
    Image,
    Link,
    List,
    ListItem,
    Node,
    Paragraph,
    Text,
)
from .registry import (
    DESTINATION_FORMATS,
    SOURCE_FORMATS,
    convert,
    parse,
    render,
)

__version__ = "0.2.0"

#: Library logging is silent until the application asks for it.
logging.getLogger(__name__).addHandler(logging.NullHandler())


__all__ = [
    "Node", "Heading", "Paragraph", "List", "ListItem",
    "Text", "CodeBlock", "Link", "Image", "HtmlBlock",
    "GeometryBlock", "Formatting",
    "GeoMdError", "UnknownFormatError", "InvalidDocumentError",
    "InvalidGeometryError", "DroppedContentWarning",
    "convert", "render", "parse",
    "SOURCE_FORMATS", "DESTINATION_FORMATS",
    "__version__",
]


def main(argv: list[str] | None = None) -> int:
    """Entry point of the ``geomd`` console script."""
    from .cli import main as cli_main

    return cli_main(argv)
