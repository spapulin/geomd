from .constants import _EXTRA_FIELDS, _FIELD_MAPPING


def parse_metadata_from_html_comment(comment: str) -> dict:
    extra_fields, field_mapping = {}, {}
    section = None
    for raw_line in comment.splitlines():

        line = raw_line.strip()
        if not line:
            continue

        if line == f"{_EXTRA_FIELDS}:":
            section = extra_fields
            continue

        if line == f"{_FIELD_MAPPING}:":
            section = field_mapping
            continue

        if line.startswith("- ") and section is not None:
            key, _, value = line[2:].partition(":")
            section[key.strip()] = value.strip()

    return {
        _EXTRA_FIELDS: extra_fields,
        _FIELD_MAPPING: field_mapping
    }


def render_metadata_as_html_comment(metadata: dict) -> str:
    comment_list = []
    for key in [_EXTRA_FIELDS, _FIELD_MAPPING]:
        if key in metadata and metadata[key]:
            comment_list.append(f"{key}:")
            for attr, value in metadata[key].items():
                comment_list.append(f"\t- {attr}: {value}")
    comments_body = "\n".join(comment_list)
    return f"<!--\n{comments_body}\n-->"