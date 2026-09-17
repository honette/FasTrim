from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QFontDatabase, QIcon, QPainter, QPalette, QPen, QPixmap
from PySide6.QtWidgets import QApplication


def apply_theme(app: QApplication) -> None:
    app.setStyle("Fusion")
    try:
        app.styleHints().setColorScheme(Qt.ColorScheme.Dark)
    except Exception:
        pass
    families = set(QFontDatabase.families())
    for name in (
        "Segoe UI",
        "Yu Gothic UI",
        "Meiryo UI",
        "Noto Sans",
        "DejaVu Sans",
    ):
        if name in families:
            font = QFont(name, 10)
            break
    else:
        font = QFont()
        font.setPointSize(10)
    app.setFont(font)

    palette = QPalette()
    bg = QColor("#1e1e1e")
    panel = QColor("#252526")
    text = QColor("#e8e8e8")
    disabled = QColor("#8a8a8a")
    highlight = QColor("#0e639c")
    button = QColor("#2d2d30")
    palette.setColor(QPalette.Window, bg)
    palette.setColor(QPalette.WindowText, text)
    palette.setColor(QPalette.Base, QColor("#141414"))
    palette.setColor(QPalette.AlternateBase, panel)
    palette.setColor(QPalette.ToolTipBase, panel)
    palette.setColor(QPalette.ToolTipText, text)
    palette.setColor(QPalette.Text, text)
    palette.setColor(QPalette.Button, button)
    palette.setColor(QPalette.ButtonText, text)
    palette.setColor(QPalette.BrightText, QColor("#ffffff"))
    palette.setColor(QPalette.Highlight, highlight)
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    palette.setColor(QPalette.PlaceholderText, QColor("#8d8d8d"))
    palette.setColor(QPalette.Disabled, QPalette.Text, disabled)
    palette.setColor(QPalette.Disabled, QPalette.ButtonText, disabled)
    palette.setColor(QPalette.Disabled, QPalette.WindowText, disabled)
    app.setPalette(palette)
    app.setStyleSheet(
        """
        QMainWindow { background: #1e1e1e; }
        QMenuBar { background: #2d2d30; color: #e8e8e8; padding: 2px; }
        QMenuBar::item:selected { background: #3e3e42; }
        QMenu { background: #2d2d30; color: #e8e8e8; }
        QMenu::item:selected { background: #0e639c; }
        QFrame#ribbon {
            background: #2d2d30;
            border-bottom: 1px solid #3e3e42;
            padding: 4px 8px;
        }
        QFrame#sidebar {
            background: #252526;
            border-left: 1px solid #3e3e42;
        }
        QLabel#sidebarTitle { color: #cccccc; font-weight: 600; }
        QListWidget {
            background: #1e1e1e;
            border: none;
            outline: none;
        }
        QListWidget::item { padding: 4px 8px; }
        QListWidget::item:selected { background: #0e639c; color: #ffffff; }
        QListWidget::item:hover { background: #3e3e42; }
        QStatusBar { background: #007acc; color: #ffffff; }
        QStatusBar QLabel { color: #ffffff; padding: 0 8px; }
        QComboBox, QSpinBox, QLineEdit {
            background: #3c3c3c;
            border: 1px solid #555;
            padding: 2px 6px;
            min-height: 22px;
        }
        QPushButton {
            background: #3c3c3c;
            border: 1px solid #555;
            padding: 4px 10px;
            min-height: 22px;
        }
        QPushButton:hover { background: #4a4a4a; }
        QPushButton:pressed { background: #2a2a2a; }
        QPushButton#cropSaveBtn {
            background: #2ea043;
            color: #ffffff;
            border: none;
            border-radius: 4px;
            padding: 4px 12px;
            font-weight: 700;
        }
        QPushButton#cropSaveBtn:hover { background: #3fb950; }
        QCheckBox { spacing: 6px; }
        QToolTip {
            background: #2d2d30;
            color: #e8e8e8;
            border: 1px solid #555;
        }
        """
    )


def asset_path(name: str) -> Path:
    base = Path(getattr(sys, "_MEIPASS", "")) if getattr(sys, "frozen", False) else None
    if base is not None:
        candidate = base / "assets" / name
        if candidate.exists():
            return candidate
    return Path(__file__).resolve().parent.parent / "assets" / name


def make_app_icon() -> QIcon:
    ico = asset_path("FasTrim.ico")
    if ico.exists():
        icon = QIcon(str(ico))
        if not icon.isNull():
            return icon
    pixmap = QPixmap(256, 256)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.setBrush(QColor("#1f6feb"))
    painter.setPen(Qt.NoPen)
    painter.drawRoundedRect(16, 16, 224, 224, 48, 48)
    pen = QPen(QColor("#ffffff"), 18, Qt.SolidLine, Qt.SquareCap, Qt.MiterJoin)
    painter.setPen(pen)
    painter.setBrush(Qt.NoBrush)
    painter.drawLine(72, 88, 72, 72)
    painter.drawLine(72, 72, 104, 72)
    painter.drawLine(184, 72, 152, 72)
    painter.drawLine(184, 72, 184, 88)
    painter.drawLine(72, 168, 72, 184)
    painter.drawLine(72, 184, 104, 184)
    painter.drawLine(184, 168, 184, 184)
    painter.drawLine(184, 184, 152, 184)
    painter.end()
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(pixmap.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation))
    return icon
