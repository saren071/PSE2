from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from pse2.games.base import GamePlugin, SaveLocation
from pse2.models.phasmo import Inventory, PlayerStats


class PhasmophobiaPlugin(GamePlugin):
    id = "phasmophobia"
    name = "Phasmophobia"

    def get_default_locations(self) -> list[SaveLocation]:
        userprofile = os.getenv("USERPROFILE", "")
        base = Path(userprofile) / "AppData" / "LocalLow" / "Kinetic Games" / "Phasmophobia"
        return [SaveLocation("Default Save", base / "SaveFile.txt")]

    def get_es3_key(self) -> str:
        return "t36gref9u84y7f43g"

    def parse_save(self, raw: dict[str, Any]) -> dict[str, Any]:
        player = PlayerStats.from_raw(raw)
        inventory = Inventory.from_raw(raw)
        return {
            "player": player,
            "inventory": inventory,
            "raw": raw,
        }

    def serialize_save(self, structured: dict[str, Any]) -> dict[str, Any]:
        player: PlayerStats = structured["player"]
        inventory: Inventory = structured["inventory"]
        base_raw: dict[str, Any] = dict(structured.get("raw", {}))

        base_raw.update(player.to_raw())
        base_raw.update(inventory.to_raw())
        return base_raw
