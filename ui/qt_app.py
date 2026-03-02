from __future__ import annotations

import sys
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QAbstractItemView,
    QApplication,
    QDialog,
    QFileDialog,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from pse2.core_es3.io import ES3Backend
from pse2.games.registry import get_all_plugins

if TYPE_CHECKING:
    from pse2.models.phasmo import PlayerStats


def resource_path(relative: str) -> Path:
    if hasattr(sys, "_MEIPASS"):
        base = Path(sys._MEIPASS)  # type: ignore[attr-defined]
    else:
        base = Path(__file__).resolve().parents[1]  # project root (folder containing pse2/)
    return base / relative



class DictEditorDialog(QDialog):
    def __init__(self, data: dict[str, Any], parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Edit value")
        self.resize(400, 300)

        # Determine mode
        if (
            isinstance(data, dict)
            and "__type" in data
            and "value" in data
            and isinstance(data["value"], dict)
        ):
            self._mode = "wrapped"
            self._outer_type = data["__type"]
            self._inner = dict(data["value"])
        else:
            self._mode = "plain"
            self._outer_type = None
            self._inner = dict(data)

        layout = QVBoxLayout(self)

        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Key", "Value"])
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(self.table)

        btn_row = QHBoxLayout()
        ok_btn = QPushButton("OK")
        cancel_btn = QPushButton("Cancel")
        ok_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(ok_btn)
        btn_row.addWidget(cancel_btn)
        layout.addLayout(btn_row)

        self._populate()

    def _populate(self):
        self.table.setRowCount(0)
        for key, val in self._inner.items():
            row = self.table.rowCount()
            self.table.insertRow(row)

            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, key_item)

            value_item = QTableWidgetItem(str(val))
            value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
            self.table.setItem(row, 1, value_item)

    def _apply_changes(self):
        updated: dict[str, Any] = {}

        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            value_item = self.table.item(row, 1)
            if not key_item or not value_item:
                continue

            key = key_item.text()
            text = value_item.text()
            try:
                val = float(text)
            except ValueError:
                val = text

            updated[key] = val

        self._inner = updated

    def accept(self) -> None:
        self._apply_changes()
        super().accept()

    def get_result(self) -> dict[str, Any]:
        if self._mode == "wrapped":
            return {
                "__type": self._outer_type,
                "value": self._inner,
            }
        return self._inner


class MainWindow(QWidget):
    def __init__(self):
        super().__init__()

        icon_path = resource_path("pse2/ui/pse2_icon.ico")
        if icon_path.is_file():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.setWindowTitle("PSE2 - Phasmophobia Save Editor")
        self.resize(800, 600)

        self.plugins = get_all_plugins()
        self.plugin = self.plugins[0]  # Phasmophobia

        self.backend: ES3Backend | None = None
        self.save_path: Path | None = None
        self.structured: dict[str, Any] | None = None

        self._build_ui()

    # ---------- UI setup ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self._build_basic_tab()
        self._build_advanced_tab()

    def _build_basic_tab(self):
        self.basic_tab = QWidget()
        basic_layout = QVBoxLayout(self.basic_tab)


        path_row = QHBoxLayout()
        path_row.addWidget(QLabel("Save file:"))

        self.path_edit = QLineEdit()
        path_row.addWidget(self.path_edit)

        basic_layout.addLayout(path_row)

   
        btn_path_row = QHBoxLayout()

        browse_btn = QPushButton("Browse…")
        browse_btn.clicked.connect(self.on_browse)
        btn_path_row.addWidget(browse_btn)

        autodetect_btn = QPushButton("Auto-detect")
        autodetect_btn.clicked.connect(self.on_autodetect)
        btn_path_row.addWidget(autodetect_btn)

        load_btn = QPushButton("Load")
        load_btn.clicked.connect(self.on_load)
        btn_path_row.addWidget(load_btn)

        basic_layout.addLayout(btn_path_row)

    
        label_width = 80

        # Money row
        money_row = QHBoxLayout()
        money_label = QLabel("Money:")
        money_label.setFixedWidth(label_width)
        money_row.addWidget(money_label)

        self.money_edit = QLineEdit()
        money_row.addWidget(self.money_edit)
        basic_layout.addLayout(money_row)

        # Experience row
        xp_row = QHBoxLayout()
        xp_label = QLabel("Experience:")
        xp_label.setFixedWidth(label_width)
        xp_row.addWidget(xp_label)

        self.xp_edit = QLineEdit()
        xp_row.addWidget(self.xp_edit)
        basic_layout.addLayout(xp_row)

        # Info label for failsafe messages
        self.info_label = QLabel("")
        self.info_label.setWordWrap(True)
        basic_layout.addWidget(self.info_label)

        # Save button row
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save")
        save_btn.clicked.connect(self.on_save)
        btn_row.addWidget(save_btn)
        basic_layout.addLayout(btn_row)

        self.tabs.addTab(self.basic_tab, "Basic")

    def _build_advanced_tab(self):
        self.advanced_tab = QWidget()
        adv_layout = QVBoxLayout(self.advanced_tab)

        self.table = QTableWidget(0, 3)
        self.table.setHorizontalHeaderLabels(["Key", "Type", "Value"])
        self.table.setEditTriggers(QAbstractItemView.AllEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectItems)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)

        adv_layout.addWidget(self.table)
        self.tabs.addTab(self.advanced_tab, "Advanced")

    # ---------- Utility ----------

    def _guess_default_path(self) -> Path | None:
        locs = self.plugin.get_default_locations()
        if locs:
            return locs[0].path
        return None

    def _show_error(self, title: str, text: str):
        QMessageBox.critical(self, title, text)

    def _show_info(self, title: str, text: str):
        QMessageBox.information(self, title, text)

    # ---------- Handlers ----------

    def on_browse(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Select Phasmophobia SaveFile.txt",
            "",
            "Text/ES3 files (*.txt *.es3);;All files (*.*)",
        )
        if filename:
            self.path_edit.setText(filename)

    def on_autodetect(self):
        """Fill the path box with the default save location if it exists."""
        path = self._guess_default_path()
        if not path:
            self._show_error("Error", "No default location defined for this game.")
            return
        self.path_edit.setText(str(path))

    def on_load(self):
        """Load data from whatever path is currently in the line edit."""
        path_str = self.path_edit.text().strip()
        if not path_str:
            path = self._guess_default_path()
            if not path:
                self._show_error("Error", "No save file specified and auto-detect failed.")
                return
            self.path_edit.setText(str(path))
        else:
            path = Path(path_str)

        if not path.is_file():
            self._show_error("Error", f"Save file not found:\n{path}")
            return

        self.save_path = path
        self.backend = ES3Backend(key=self.plugin.get_es3_key())

        try:
            raw = self.backend.load_from_file(path)
            self.structured = self.plugin.parse_save(raw)
            self._populate_basic_fields()
            self._populate_advanced_table()
            self._show_info("Loaded", f"Loaded save from:\n{path}")
        except Exception as exc:
            self._show_error("Error", f"Failed to load save:\n{exc}")

    def on_save(self):
        if not self.save_path or not self.backend or not self.structured:
            self._show_error("Error", "No save loaded.")
            return

        player: PlayerStats = self.structured["player"]


        if player.money is not None:
            money_text = self.money_edit.text().strip()
            if money_text.upper() != "ERROR" and money_text != "":
                try:
                    player.money = int(money_text)
                except ValueError:
                    self._show_error("Error", "Money must be an integer.")
                    return


        if player.experience is not None:
            xp_text = self.xp_edit.text().strip()
            if xp_text.upper() != "ERROR" and xp_text != "":
                try:
                    player.experience = int(xp_text)
                except ValueError:
                    self._show_error("Error", "Experience must be an integer.")
                    return

        self.structured["player"] = player


        self._apply_advanced_changes()

        try:
            new_raw = self.plugin.serialize_save(self.structured)
            self.backend.save_to_file(self.save_path, new_raw)
            self._show_info("Saved", "Save updated (backup created).")
        except Exception as exc:
            self._show_error("Error", f"Failed to save:\n{exc}")

    # ---------- Basic tab helpers ----------

    def _populate_basic_fields(self):
        player: PlayerStats = self.structured["player"]
        messages: list[str] = []

        if player.money is None:
            self.money_edit.setText("ERROR")
            self.money_edit.setReadOnly(True)
            messages.append("Money key not found (PlayersMoney).")
        else:
            self.money_edit.setReadOnly(False)
            self.money_edit.setText(str(player.money))

        if player.experience is None:
            self.xp_edit.setText("ERROR")
            self.xp_edit.setReadOnly(True)
            messages.append("Experience key not found (Experience).")
        else:
            self.xp_edit.setReadOnly(False)
            self.xp_edit.setText(str(player.experience))

        if messages:
            self.info_label.setText(
                "Warning:\n" + "\n".join(messages) + "\nUse the Advanced tab to inspect keys."
            )
        else:
            self.info_label.setText("")

    # ---------- Advanced tab helpers ----------

    def _populate_advanced_table(self):
        self.table.setRowCount(0)
        if not self.structured:
            return
        raw = self.structured.get("raw", {})

        for key, entry in raw.items():
            row = self.table.rowCount()
            self.table.insertRow(row)


            key_item = QTableWidgetItem(str(key))
            key_item.setFlags(key_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 0, key_item)


            if isinstance(entry, dict) and "value" in entry:
                val = entry["value"]
                t = str(entry.get("__type", type(val).__name__))
            else:
                val = entry
                t = type(val).__name__

            if isinstance(val, bool):
                t_display = "bool"
            elif isinstance(val, int):
                t_display = "int"
            elif isinstance(val, float):
                t_display = "float"
            elif isinstance(val, str):
                t_display = "string"
            else:
                t_display = t


            type_item = QTableWidgetItem(t_display)
            type_item.setFlags(type_item.flags() & ~Qt.ItemIsEditable)
            self.table.setItem(row, 1, type_item)


            if t_display == "bool":
                btn = QPushButton("True" if bool(val) else "False")
                btn.setCheckable(True)
                btn.setChecked(bool(val))
                btn.setText("True" if btn.isChecked() else "False")
                btn.clicked.connect(
                    lambda checked, b=btn: b.setText("True" if checked else "False")
                )
                btn.setProperty("pse2_key", str(key))
                self.table.setCellWidget(row, 2, btn)
            elif t_display in ("int", "float", "string"):
                value_item = QTableWidgetItem(str(val))
                value_item.setFlags(value_item.flags() | Qt.ItemIsEditable)
                self.table.setItem(row, 2, value_item)
            else:
                btn = QPushButton("Edit")
                btn.setProperty("pse2_key", str(key))
                btn.clicked.connect(self.on_edit_complex_value_clicked)
                self.table.setCellWidget(row, 2, btn)

    def on_edit_complex_value_clicked(self):
        if not self.structured:
            return
        raw = self.structured.get("raw", {})

        sender = self.sender()
        if not isinstance(sender, QPushButton):
            return

        key = sender.property("pse2_key")
        if key is None:
            return

        entry = raw.get(key)
        if not isinstance(entry, dict):
            return

        dlg = DictEditorDialog(entry, self)
        if dlg.exec() == QDialog.Accepted:
            new_entry = dlg.get_result()
            raw[key] = new_entry
            self.structured["raw"] = raw

    def _apply_advanced_changes(self):
        if not self.structured:
            return
        raw = self.structured.get("raw", {})

        for row in range(self.table.rowCount()):
            key_item = self.table.item(row, 0)
            type_item = self.table.item(row, 1)
            if not key_item or not type_item:
                continue

            key = key_item.text()
            t = type_item.text()
            entry = raw.get(key)


            if t == "bool":
                btn = self.table.cellWidget(row, 2)
                if isinstance(btn, QPushButton):
                    val_bool = btn.isChecked()
                    if isinstance(entry, dict) and "value" in entry:
                        entry["value"] = val_bool
                        raw[key] = entry
                    else:
                        raw[key] = val_bool
                continue

            cell_widget = self.table.cellWidget(row, 2)
            if cell_widget is not None and t != "bool":
                continue

            value_item = self.table.item(row, 2)
            if not value_item:
                continue
            text = value_item.text()

            if isinstance(entry, dict) and "value" in entry:
                if t == "int":
                    try:
                        entry["value"] = int(text)
                    except ValueError:
                        continue
                elif t == "float":
                    try:
                        entry["value"] = float(text)
                    except ValueError:
                        continue
                else:
                    entry["value"] = text
                raw[key] = entry
            else:
                if t == "int":
                    try:
                        raw[key] = int(text)
                    except ValueError:
                        continue
                elif t == "float":
                    try:
                        raw[key] = float(text)
                    except ValueError:
                        continue
                else:
                    raw[key] = text

        self.structured["raw"] = raw


def run_qt():
    import sys
    from pathlib import Path

    app = QApplication(sys.argv)

    qss_path = Path(__file__).with_name("theme_dark.qss")
    if qss_path.is_file():
        app.setStyleSheet(qss_path.read_text(encoding="utf-8"))

    icon_path = Path(__file__).with_name("icon.ico")
    if icon_path.is_file():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = MainWindow()
    window.show()
    sys.exit(app.exec())