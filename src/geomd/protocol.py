from typing import Protocol

from geomd.models import Node


class Parser(Protocol):
    def parse(self, text: str) -> list[Node]: ...

class Renderer(Protocol):
    def render(
            self,
            nodes: list[Node],
            *,
            as_dict: bool,
            auto_contents: bool,
            contents_title: str
    ) -> str | dict: ...

