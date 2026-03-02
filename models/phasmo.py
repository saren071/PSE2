from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class PlayerStats:
    money: int | None
    experience: int | None

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> PlayerStats:
        money_entry: Any | None = raw.get("PlayersMoney")
        exp_entry: Any | None = raw.get("Experience")

        money = money_entry.get("value") if isinstance(money_entry, dict) else None
        experience = exp_entry.get("value") if isinstance(exp_entry, dict) else None

        return cls(money=money, experience=experience)

    def to_raw(self) -> dict[str, Any]:
        """Only write keys that are present (None means missing)."""
        out: dict[str, Any] = {}
        if self.money is not None:
            out["PlayersMoney"] = {"__type": "int", "value": int(self.money)}
        if self.experience is not None:
            out["Experience"] = {"__type": "int", "value": int(self.experience)}
        return out


@dataclass
class InventoryItem:
    name: str
    amount: int


@dataclass
class Inventory:
    items: list[InventoryItem]

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> Inventory:
        return cls(items=[])

    def to_raw(self) -> dict[str, Any]:
        return {}
