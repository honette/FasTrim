from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QSpinBox,
    QVBoxLayout,
)

from fastrim.config import Settings
from fastrim.constants import PRESET_DATETIME, PRESET_SEQ, PRESET_SEQ_ONLY
from fastrim.naming import example_name


class NamingDialog(QDialog):
    def __init__(self, settings: Settings, sample_name: str = "IMG_1234.jpg", parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Auto-save name")
        self._sample = sample_name
        self._ext = Path(sample_name).suffix or ".jpg"

        layout = QVBoxLayout(self)
        group = QGroupBox("Filename pattern")
        group_layout = QVBoxLayout(group)
        self.seq_radio = QRadioButton("Original name + sequence")
        self.datetime_radio = QRadioButton("Original name + date/time (to the second)")
        self.seq_only_radio = QRadioButton("Sequence only")
        self._group = QButtonGroup(self)
        for radio in (self.seq_radio, self.datetime_radio, self.seq_only_radio):
            self._group.addButton(radio)
            group_layout.addWidget(radio)
        layout.addWidget(group)

        form = QFormLayout()
        self.digits = QSpinBox()
        self.digits.setRange(1, 8)
        self.digits.setValue(settings.seq_digits)
        form.addRow("Sequence digits", self.digits)
        self.subfolder = QLineEdit(settings.subfolder)
        self.subfolder.setPlaceholderText("Empty = same folder (e.g. trim)")
        form.addRow("Subfolder", self.subfolder)
        layout.addLayout(form)

        self.preview = QLabel()
        self.preview.setWordWrap(True)
        self.preview.setStyleSheet("color: #9cdcfe;")
        layout.addWidget(self.preview)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        preset = settings.naming_preset
        if preset == PRESET_DATETIME:
            self.datetime_radio.setChecked(True)
        elif preset == PRESET_SEQ_ONLY:
            self.seq_only_radio.setChecked(True)
        else:
            self.seq_radio.setChecked(True)

        for widget in (self.seq_radio, self.datetime_radio, self.seq_only_radio, self.digits, self.subfolder):
            if isinstance(widget, QLineEdit):
                widget.textChanged.connect(self._refresh_preview)
            elif isinstance(widget, QSpinBox):
                widget.valueChanged.connect(self._refresh_preview)
            else:
                widget.toggled.connect(self._refresh_preview)
        self._refresh_preview()
        self.resize(420, 280)

    def preset(self) -> str:
        if self.datetime_radio.isChecked():
            return PRESET_DATETIME
        if self.seq_only_radio.isChecked():
            return PRESET_SEQ_ONLY
        return PRESET_SEQ

    def apply_to(self, settings: Settings) -> None:
        settings.naming_preset = self.preset()
        settings.seq_digits = self.digits.value()
        settings.subfolder = self.subfolder.text().strip()

    def _refresh_preview(self) -> None:
        name = example_name(
            self._sample,
            preset=self.preset(),
            digits=self.digits.value(),
            subfolder=self.subfolder.text(),
            ext=self._ext,
        )
        self.preview.setText(f"Preview: {name}")


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, sample_name: str = "IMG_1234.jpg", parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self._settings = settings
        self._sample = sample_name

        layout = QVBoxLayout(self)
        self.auto_save = QCheckBox("Auto-save (crop as soon as a region is selected)")
        self.auto_save.setChecked(settings.auto_save)
        layout.addWidget(self.auto_save)

        name_row = QHBoxLayout()
        self.naming_label = QLabel()
        self.naming_btn = QPushButton("Auto-save name…")
        self.naming_btn.clicked.connect(self._edit_naming)
        name_row.addWidget(self.naming_label, 1)
        name_row.addWidget(self.naming_btn)
        layout.addLayout(name_row)

        self.auto_resize = QCheckBox("Auto-resize (match long side when an image is loaded)")
        self.auto_resize.setChecked(settings.auto_resize)
        layout.addWidget(self.auto_resize)

        self.dont_upscale = QCheckBox("Do not enlarge smaller images")
        self.dont_upscale.setChecked(settings.dont_upscale)
        layout.addWidget(self.dont_upscale)

        form = QFormLayout()
        self.output_format = QComboBox()
        self.output_format.addItem("Keep original format", "original")
        self.output_format.addItem("JPEG", "jpeg")
        self.output_format.addItem("PNG", "png")
        self.output_format.addItem("WebP", "webp")
        index = self.output_format.findData(settings.output_format)
        self.output_format.setCurrentIndex(max(0, index))
        form.addRow("Output format", self.output_format)

        self.quality = QSpinBox()
        self.quality.setRange(1, 100)
        self.quality.setValue(settings.jpeg_quality)
        self.quality.setSuffix(" %")
        form.addRow("JPEG / WebP quality", self.quality)
        layout.addLayout(form)

        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._refresh_naming_label()
        self.resize(460, 280)

    def apply_to(self, settings: Settings) -> None:
        settings.auto_save = self.auto_save.isChecked()
        settings.auto_resize = self.auto_resize.isChecked()
        settings.dont_upscale = self.dont_upscale.isChecked()
        settings.output_format = str(self.output_format.currentData())
        settings.jpeg_quality = self.quality.value()

    def _edit_naming(self) -> None:
        dialog = NamingDialog(self._settings, self._sample, self)
        if dialog.exec() == QDialog.Accepted:
            dialog.apply_to(self._settings)
            self._refresh_naming_label()

    def _refresh_naming_label(self) -> None:
        sample = example_name(
            self._sample,
            preset=self._settings.naming_preset,
            digits=self._settings.seq_digits,
            subfolder=self._settings.subfolder,
            ext=Path(self._sample).suffix or ".jpg",
        )
        self.naming_label.setText(f"Name: {sample}")


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("Keyboard shortcuts")
        layout = QVBoxLayout(self)
        text = QLabel(
            "\n".join(
                [
                    "Ctrl+O          Open image",
                    "Ctrl+S / Enter  Save selection",
                    "Esc             Clear selection",
                    "Left / Right    Previous / next image",
                    "Ctrl+Left/Right Rotate 90° CCW / CW",
                    "Mouse wheel     Zoom toward cursor",
                    "Middle-drag / Ctrl-drag  Pan",
                    "Ctrl+C          Copy selection (or whole image)",
                ]
            )
        )
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
