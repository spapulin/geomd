"""Exception types raised by :mod:`geomd`.

All errors derive from :class:`GeoMdError`, so callers can catch one type
instead of guessing which layer (parser, renderer, CLI) failed.
"""

from __future__ import annotations


class GeoMdError(ValueError):
    """Base class for every error raised by geomd."""


class UnknownFormatError(GeoMdError):
    """A source or destination format is not registered."""

    def __init__(self, fmt: str, known: list[str]) -> None:
        self.fmt = fmt
        self.known = known
        super().__init__(
            f"unknown format {fmt!r}; known formats: {', '.join(sorted(known))}"
        )


class InvalidDocumentError(GeoMdError):
    """The input text cannot be read as the declared format."""


class InvalidGeometryError(GeoMdError):
    """A ``geometry`` fenced block does not hold a GeoJSON geometry."""

    def __init__(self, reason: str, line: int | None = None, snippet: str = "") -> None:
        self.reason = reason
        self.line = line
        self.snippet = snippet
        where = f" (line {line})" if line is not None else ""
        detail = f": {snippet.strip()[:80]}" if snippet.strip() else ""
        super().__init__(f"invalid geometry block{where}: {reason}{detail}")


class DroppedContentWarning(UserWarning):
    """A section held content that the destination format cannot represent."""
