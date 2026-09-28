from geomd.models import Node, Heading, Paragraph, CodeBlock, Text, Link, Image, List, ListItem


class MarkdownRenderer:
    """Render document nodes back to Markdown text."""

    def render(self, nodes: list[Node]) -> str:
        return self._to_markdown(nodes)

    def _to_markdown(self, nodes: list[Node]) -> str:
        """Convert each block node to its Markdown form, joined by blank lines."""

        blocks: list[str] = []
        for node in nodes:
            if isinstance(node, Heading):
                blocks.append("#" * node.level + " " + self._render_inline(node.children))
            elif isinstance(node, Paragraph):
                blocks.append(self._render_inline(node.children))
            elif isinstance(node, List):
                blocks.append(self._render_list(node.children, ordered=node.ordered))
            elif isinstance(node, CodeBlock):
                language = node.language or ""
                blocks.append(f"```{language}\n{node.raw}\n```")
            else:
                raise ValueError(f"No such block node: {node.NODE_TYPE}")
        return "\n\n".join(blocks) + "\n"

    def _render_list(
            self, nodes:
            list[Node],
            ordered: bool = False,
            indent: int = 0
    ) -> str:
        """Render list items as Markdown bullets or numbered entries."""
        lines: list[str] = []
        pad = " " * indent

        for i, item in enumerate(nodes):
            marker = f"{i + 1}. " if ordered else "- "
            body = self._render_inline(item.children).strip()
            body_lines = body.splitlines() or [""]

            # First line carries the marker; continuation lines are indented
            # to line up with the item's text
            lines.append(pad + marker + body_lines[0])
            continuation = " " * len(marker)
            for line in body_lines[1:]:
                lines.append(pad + continuation + line)

        return "\n".join(lines)

    def _render_inline(self, nodes: list[Node]) -> str:
        """Flatten inline nodes (Text/Link/Image) to a single string."""

        result: list[str] = []
        for node in nodes:
            if isinstance(node, Text):
                result.append(node.raw)
            elif isinstance(node, Link):
                title = f'"{node.title}"' if node.title else ""
                result.append(f"[{title}]({node.url})")
            elif isinstance(node, Image):
                # Standard Markdown: ![alt](url "title")
                title = f' "{node.title}"' if node.title else ""
                result.append(f"![{node.alt}]({node.url}{title})")
            else:
                raise ValueError(f"No such inline node: {node.NODE_TYPE}")
        return "".join(result)
