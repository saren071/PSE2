from __future__ import annotations

import argparse
from pathlib import Path
from typing import TYPE_CHECKING

from pse2.core_es3.io import ES3Backend
from pse2.games.registry import get_all_plugins, get_plugin_by_id

if TYPE_CHECKING:
    from pse2.models.phasmo import PlayerStats


def run_cli() -> None:
    parser = argparse.ArgumentParser(
        description="PSE2 - Phasmophobia / ES3 game save editor (CLI)"
    )
    parser.add_argument(
        "game",
        nargs="?",
        default="phasmophobia",
        help="Game plugin id (default: phasmophobia, or 'list' to list plugins)",
    )
    parser.add_argument(
        "--file",
        type=str,
        help="Path to ES3 save file. If omitted, the game's default location is used.",
    )
    parser.add_argument(
        "--set-money",
        type=int,
        help="Set player money to this value.",
    )
    parser.add_argument(
        "--set-xp",
        type=int,
        help="Set player experience (XP) to this value.",
    )

    args = parser.parse_args()

    if args.game == "list":
        print("Available game plugins:")
        for plugin in get_all_plugins():
            print(f"  {plugin.id} - {plugin.name}")
        return

    plugin = get_plugin_by_id(args.game)
    key = plugin.get_es3_key()

    if args.file:
        save_path = Path(args.file)
    else:
        default_locations = plugin.get_default_locations()
        if not default_locations:
            raise SystemExit("No default locations defined for this game.")
        save_path = default_locations[0].path

    backend = ES3Backend(key=key)

    print(f"Loading save from: {save_path}")
    raw = backend.load_from_file(save_path)
    structured = plugin.parse_save(raw)

    player: PlayerStats = structured["player"]
    print(f"Current money: {player.money}, experience: {player.experience}")

    changed = False

    if args.set_money is not None:
        print(f"Setting money -> {args.set_money}")
        player.money = args.set_money
        changed = True

    if args.set_xp is not None:
        print(f"Setting experience -> {args.set_xp}")
        player.experience = args.set_xp
        changed = True

    if changed:
        structured["player"] = player
        new_raw = plugin.serialize_save(structured)
        backend.save_to_file(save_path, new_raw)
        print("Save updated (backup created in the save directory).")
    else:
        print("No changes requested; save not modified.")
