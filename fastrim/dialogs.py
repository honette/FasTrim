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
        self.setWindowTitle("自動保存名")
        self._sample = sample_name
        self._ext = Path(sample_name).suffix or ".jpg"

        layout = QVBoxLayout(self)
        group = QGroupBox("ファイル名の付け方")
        group_layout = QVBoxLayout(group)
        self.seq_radio = QRadioButton("元ファイル名 + 連番")
        self.datetime_radio = QRadioButton("元ファイル名 + 日時（秒まで）")
        self.seq_only_radio = QRadioButton("連番のみ")
        self._group = QButtonGroup(self)
        for radio in (self.seq_radio, self.datetime_radio, self.seq_only_radio):
            self._group.addButton(radio)
            group_layout.addWidget(radio)
        layout.addWidget(group)

        form = QFormLayout()
        self.digits = QSpinBox()
        self.digits.setRange(1, 8)
        self.digits.setValue(settings.seq_digits)
        form.addRow("連番の桁数", self.digits)
        self.subfolder = QLineEdit(settings.subfolder)
        self.subfolder.setPlaceholderText("空なら同じフォルダ（例: trim）")
        form.addRow("サブフォルダ", self.subfolder)
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
        self.preview.setText(f"プレビュー: {name}")


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, sample_name: str = "IMG_1234.jpg", parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("設定")
        self._settings = settings
        self._sample = sample_name

        layout = QVBoxLayout(self)
        self.auto_save = QCheckBox("自動保存（範囲を決めた時点でクロップ保存）")
        self.auto_save.setChecked(settings.auto_save)
        layout.addWidget(self.auto_save)

        name_row = QHBoxLayout()
        self.naming_label = QLabel()
        self.naming_btn = QPushButton("自動保存名…")
        self.naming_btn.clicked.connect(self._edit_naming)
        name_row.addWidget(self.naming_label, 1)
        name_row.addWidget(self.naming_btn)
        layout.addLayout(name_row)

        self.auto_resize = QCheckBox("自動リサイズ（画像ロード時に長辺を揃える）")
        self.auto_resize.setChecked(settings.auto_resize)
        layout.addWidget(self.auto_resize)

        self.dont_upscale = QCheckBox("小さい画像は拡大しない")
        self.dont_upscale.setChecked(settings.dont_upscale)
        layout.addWidget(self.dont_upscale)

        form = QFormLayout()
        self.output_format = QComboBox()
        self.output_format.addItem("元の形式のまま", "original")
        self.output_format.addItem("JPEG", "jpeg")
        self.output_format.addItem("PNG", "png")
        self.output_format.addItem("WebP", "webp")
        index = self.output_format.findData(settings.output_format)
        self.output_format.setCurrentIndex(max(0, index))
        form.addRow("出力形式", self.output_format)

        self.quality = QSpinBox()
        self.quality.setRange(1, 100)
        self.quality.setValue(settings.jpeg_quality)
        self.quality.setSuffix(" %")
        form.addRow("JPEG / WebP 品質", self.quality)
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
        self.naming_label.setText(f"保存名: {sample}")


class ShortcutsDialog(QDialog):
    def __init__(self, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self.setWindowTitle("ショートカット")
        layout = QVBoxLayout(self)
        text = QLabel(
            "\n".join(
                [
                    "Ctrl+O        画像を開く",
                    "Ctrl+S / Enter 選択範囲を保存",
                    "Esc           選択を解除",
                    "← / →         前 / 次の画像",
                    "Ctrl+← / Ctrl+→  左 / 右に90度回転",
                    "ホイール      カーソル位置を中心に拡大縮小",
                    "中ドラッグ / Ctrl+ドラッグ  パン",
                    "Ctrl+C        選択範囲（なければ全体）をクリップボードへ",
                ]
            )
        )
        text.setTextInteractionFlags(Qt.TextSelectableByMouse)
        layout.addWidget(text)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
