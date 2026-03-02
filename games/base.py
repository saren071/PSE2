from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from pathlib import Path


@dataclass
class SaveLocation:
    label: str
    path: Path


class GamePlugin(Protocol):
    id: str
    name: str

    def get_default_locations(self) -> list[SaveLocation]:
        ...

    def get_es3_key(self) -> str:
        ...

    def parse_save(self, raw: dict[str, Any]) -> dict[str, Any]:
        ...

    def serialize_save(self, structured: dict[str, Any]) -> dict[str, Any]:
        ...
