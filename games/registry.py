from __future__ import annotations

from typing import TYPE_CHECKING

from pse2.games.phasmophobia.plugin import PhasmophobiaPlugin

if TYPE_CHECKING:
    from pse2.games.base import GamePlugin


def get_all_plugins() -> list[GamePlugin]:
    return [
        PhasmophobiaPlugin(),
    ]


def get_plugin_by_id(plugin_id: str) -> GamePlugin:
    for plugin in get_all_plugins():
        if plugin.id == plugin_id:
            return plugin
    raise KeyError(f"No plugin with id '{plugin_id}'")
