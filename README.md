# PSE2 – Phasmophobia Save Editor

PSE2 is a Phasmophobia save editor, continuation of my previous PSE.  

## Features

- 🖥️ **GUI by default (PySide6)**
  - `Money` and `Experience` fields on the Basic tab.
  - Auto‑detects the default Phasmophobia save path.
  - Manual browse + explicit “Load” and “Save” buttons.
- 🧪 **Type‑aware editing**
  - Integers and floats editable directly in the table.
  - Boolean values edited via toggle buttons (no typing `true` / `false`).
- 🧩 **Advanced tab**
  - Lists *all* keys in the save file in a table (Key / Type / Value).
  - Primitive values are editable inline.
  - Complex/dict values have an **Edit** button that opens a child dialog.
- 🗂️ **Child dialog for complex values**
  - Handles both plain dicts and ES3 style `{"__type": ..., "value": {...}}`.
  - Shows each sub‑key as a row (e.g. `r`, `g`, `b`, `a` for colors).
- 🧷 **Safe editing**
  - Money/XP only written if those keys exist; otherwise you see `ERROR` and the field is read‑only.
  - Unknown keys are preserved so future game updates are less likely to break saves.
  - Automatic backup (`SaveFile.txt.bak-YYYYMMDD-HHMMSS`) on save.
- 🧮 **CLI mode still available**
  - Simple commands for quick edits or scripting.

---

## Installation

You need Python 3.10+.

```bash
pip install es3-modifier PySide6
```

Clone the repository and make sure you’re in the folder that contains the pse2/ package:

```bash
git clone https://github.com/nikidziuba/PSE2.git
cd PSE2
```

Running from source
GUI (recommended)

```bash
python -m pse2
```

Or explicitly:

```bash
python -m pse2 gui
```

CLI

```bash
python -m pse2 cli --set-money 1000 --set-xp 5000
```

CLI options:

```bash
    game – plugin id (default: phasmophobia, or list to list plugins)

    --file PATH – custom save file path (otherwise the default location is used)

    --set-money N

    --set-xp N
```

Usage – GUI

- [ ] Select the save file

  - Click Browse… to choose SaveFile.txt manually

  - Click Auto‑detect to fill in the default Phasmophobia path.

- [ ] Click Load to load and parse the file.

---

- [ ] On the Basic tab:

  - Edit Money and Experience.

  - If a field shows ERROR, that key wasn’t found and is locked to keep the save safe.

- [ ] On the Advanced tab:

  - Edit primitive values (int / float / string) directly.

    - Use the True/False toggle for boolean values.

    - Click Edit for complex values (dicts, colors, etc.) to open the child dialog.

      - In the child dialog:

        - Each entry appears as Key | Value.

        - Adjust values; numeric input is stored as float when possible.

        - Click OK to apply changes back to the main save structure.

- [ ] Back on the Basic tab, click Save.

  - A timestamped backup of the original save is created in the same directory.

Project structure

```text
pse2/
  __init__.py
  __main__.py          # python -m pse2 entry point
  main.py              # dispatches GUI/CLI
  core_es3/
    __init__.py
    io.py              # ES3 encryption/decryption + backup
  games/
    __init__.py
    base.py            # GamePlugin protocol
    registry.py        # plugin registry
    phasmophobia/
      __init__.py
      plugin.py        # Phasmophobia-specific logic
  models/
    __init__.py
    phasmo.py          # PlayerStats, Inventory model
  ui/
    __init__.py
    cli.py             # CLI interface
    qt_app.py          # PySide6 GUI (Basic + Advanced tabs)
    theme_dark.qss     # Dark GUI theme
    pse2_icon.ico      # Application icon
```

Safety notes

- Editing game saves can corrupt data if used incorrectly.

- Always keep backups (PSE2 creates a backup automatically on save, but you should still archive important saves).

- Use at your own risk; this project is not affiliated with or endorsed by the Phasmophobia developers.

Credits

Easy Save 3 support via es3-modifier.

GUI built with PySide6.
