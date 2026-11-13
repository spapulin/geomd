from __future__ import annotations

import logging

from .constants import _EXTRA_FIELDS, _FIELD_MAPPING

logger = logging.getLogger(__name__)


def parse_metadata_from_html_comment(comment: str) -> dict:
    """Read the ``field_mapping`` / ``extra_fields`` lists of a metadata comment.

    Returns a dict with both keys, each mapping a name to its value.  Lines
    that cannot be read are reported instead of being dropped in silence.
    """
    extra_fields: dict[str, str] = {}
    field_mapping: dict[str, str] = {}
    sections = {_EXTRA_FIELDS: extra_fields, _FIELD_MAPPING: field_mapping}
    section = None

    for raw_line in comment.splitlines():

        line = raw_line.strip()
        if not line:
            continue

        header = line.rstrip(":")
        if line.endswith(":") and header in sections:
            section = sections[header]
            continue

        if line.startswith(("<!--", "-->")):
            continue

        if section is None:
            logger.warning("Ignoring line in metadata comment without a section: %r", line)
            continue

        if not line.startswith("- "):
            logger.warning("Ignoring metadata line that is not a '- name: value' item: %r", line)
            continue

        key, _, value = line[2:].partition(":")
        key = key.strip()
        if not key:
            logger.warning("Ignoring metadata item with an empty name: %r", line)
            continue
        section[key] = value.strip()

    return {
        _EXTRA_FIELDS: extra_fields,
        _FIELD_MAPPING: field_mapping
    }


def render_metadata_as_html_comment(metadata: dict) -> str:
    """Write ``extra_fields`` and ``field_mapping`` back as an HTML comment."""
    comment_list = []
    for key in [_EXTRA_FIELDS, _FIELD_MAPPING]:
        items = metadata.get(key) or {}
        if isinstance(items, list):
            # A list of names (the GeoJSON ``_metadata`` form) carries no values.
            items = {name: "" for name in items}
        if not items:
            continue
        comment_list.append(f"{key}:")
        for attr, value in items.items():
            comment_list.append(f"\t- {attr}: {_single_line(value)}")
    comments_body = "\n".join(comment_list)
    return f"<!--\n{comments_body}\n-->"


def _single_line(value: object) -> str:
    """Flatten a value so one metadata item stays on one line."""
    if value is None:
        return ""
    text = str(value)
    if "\n" in text or "\r" in text:
        logger.warning("Metadata value contains a line break; it is written on one line")
        text = " ".join(text.split())
    return text
