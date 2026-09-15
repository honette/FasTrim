from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image
from PySide6.QtCore import QLocale, QStandardPaths, Qt, QUrl
from PySide6.QtGui import QAction, QDesktopServices, QImage, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSpinBox,
    QSplitter,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from fastrim import __version__
from fastrim.canvas import ImageCanvas
from fastrim.config import Settings, load_settings, save_settings
from fastrim.constants import (
    APP_NAME,
    ASPECT_CHOICES,
    LONG_SIDE_CHOICES,
    OPEN_FILTER,
    ORG_NAME,
    ZOOM_CHOICES,
)
from fastrim.dialogs import SettingsDialog, ShortcutsDialog
from fastrim.imageops import (
    crop_image,
    effective_ext,
    is_image_file,
    list_images,
    load_image,
    render_working,
    save_image,
)
from fastrim.dnd import first_dropped_image
from fastrim.naming import next_dest_path
from fastrim.theme import apply_theme, make_app_icon


def pil_to_qpixmap(image: Image.Image) -> QPixmap:
    if image.mode == "RGB":
        data = image.tobytes("raw", "RGB")
        qimage = QImage(data, image.width, image.height, image.width * 3, QImage.Format_RGB888)
    else:
        converted = image.convert("RGBA")
        data = converted.tobytes("raw", "RGBA")
        qimage = QImage(
            data,
            converted.width,
            converted.height,
            converted.width * 4,
            QImage.Format_RGBA8888,
        )
    return QPixmap.fromImage(qimage.copy())


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings | None = None) -> None:
        super().__init__()
        self.settings = settings or load_settings()
        self.path: Path | None = None
        self.source: Image.Image | None = None
        self.working: Image.Image | None = None
        self.rotation = 0
        self.long_side: int | None = None
        self.folder_files: list[Path] = []

        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(make_app_icon())
        self.setAcceptDrops(True)
        self.resize(self.settings.window_w, self.settings.window_h)
        if self.settings.window_x >= 0 and self.settings.window_y >= 0:
            self.move(self.settings.window_x, self.settings.window_y)

        self._build_menu()
        self._build_ui()
        self._bind_shortcuts()
        self._apply_settings_to_widgets()
        self.canvas.set_zoom_mode(self.settings.zoom_mode)
        self._update_status()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("&File")
        open_act = QAction("&Open…", self)
        open_act.setShortcut(QKeySequence.Open)
        open_act.triggered.connect(self.open_dialog)
        file_menu.addAction(open_act)

        self.next_act = QAction("&Next image", self)
        self.next_act.setShortcut(QKeySequence(Qt.Key_Right))
        self.next_act.triggered.connect(lambda: self.step_file(1))
        file_menu.addAction(self.next_act)

        self.prev_act = QAction("&Previous image", self)
        self.prev_act.setShortcut(QKeySequence(Qt.Key_Left))
        self.prev_act.triggered.connect(lambda: self.step_file(-1))
        file_menu.addAction(self.prev_act)

        folder_act = QAction("Open &folder", self)
        folder_act.triggered.connect(self.open_current_folder)
        file_menu.addAction(folder_act)
        file_menu.addSeparator()

        settings_act = QAction("&Settings…", self)
        settings_act.triggered.connect(self.open_settings)
        file_menu.addAction(settings_act)
        file_menu.addSeparator()

        exit_act = QAction("E&xit", self)
        exit_act.setShortcut(QKeySequence("Ctrl+Q"))
        exit_act.triggered.connect(self.close)
        file_menu.addAction(exit_act)

        help_menu = self.menuBar().addMenu("&Help")
        shortcut_act = QAction("&Keyboard shortcuts", self)
        shortcut_act.triggered.connect(lambda: ShortcutsDialog(self).exec())
        help_menu.addAction(shortcut_act)
        about_act = QAction("&About", self)
        about_act.triggered.connect(self.show_about)
        help_menu.addAction(about_act)

    def _build_ui(self) -> None:
        root = QWidget()
        root.setAcceptDrops(True)
        root_layout = QVBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        root_layout.addWidget(self._build_ribbon())

        self.splitter = QSplitter(Qt.Horizontal)
        self.canvas = ImageCanvas()
        self.canvas.cursorMoved.connect(self._on_cursor)
        self.canvas.selectionChanged.connect(self._on_selection)
        self.canvas.cropSaveRequested.connect(self.save_crop)
        self.canvas.zoomChanged.connect(self._on_zoom_changed)
        self.canvas.openRequested.connect(self.open_dialog)
        self.canvas.filesDropped.connect(self.open_path)
        self.splitter.addWidget(self.canvas)
        self.splitter.addWidget(self._build_sidebar())
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 0)
        if self.settings.splitter and len(self.settings.splitter) == 2:
            self.splitter.setSizes(self.settings.splitter)
        root_layout.addWidget(self.splitter, 1)
        self.setCentralWidget(root)

        status = QStatusBar()
        self.setStatusBar(status)
        self.coord_label = QLabel("Pos: —")
        self.sel_label = QLabel("Sel: —")
        self.img_label = QLabel("Image: —")
        self.zoom_label = QLabel("Zoom: —")
        self.msg_label = QLabel("")
        self.msg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        for widget in (self.coord_label, self.sel_label, self.img_label, self.zoom_label):
            status.addWidget(widget)
        status.addWidget(self.msg_label, 1)

    def _build_ribbon(self) -> QFrame:
        ribbon = QFrame()
        ribbon.setObjectName("ribbon")
        layout = QHBoxLayout(ribbon)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)

        layout.addWidget(QLabel("Zoom"))
        self.zoom_combo = QComboBox()
        for label, value in ZOOM_CHOICES:
            self.zoom_combo.addItem(label, value)
        self.zoom_combo.setMinimumWidth(90)
        self.zoom_combo.currentIndexChanged.connect(self._on_zoom_combo)
        layout.addWidget(self.zoom_combo)

        self.rot_left_btn = QPushButton("90° CCW")
        self.rot_left_btn.clicked.connect(lambda: self.rotate(False))
        self.rot_right_btn = QPushButton("90° CW")
        self.rot_right_btn.clicked.connect(lambda: self.rotate(True))
        layout.addWidget(self.rot_left_btn)
        layout.addWidget(self.rot_right_btn)

        layout.addWidget(self._separator())

        layout.addWidget(QLabel("Long side"))
        self.resize_combo = QComboBox()
        self.resize_combo.addItem("Original", 0)
        for length in LONG_SIDE_CHOICES:
            self.resize_combo.addItem(str(length), length)
        self.resize_combo.setMinimumWidth(110)
        self.resize_combo.currentIndexChanged.connect(self._on_resize_combo)
        layout.addWidget(self.resize_combo)

        layout.addWidget(self._separator())

        self.grid_cb = QCheckBox("Grid snap")
        self.grid_cb.toggled.connect(self._on_grid_toggled)
        layout.addWidget(self.grid_cb)
        self.grid_spin = QSpinBox()
        self.grid_spin.setRange(2, 512)
        self.grid_spin.setSuffix(" px")
        self.grid_spin.valueChanged.connect(self._on_grid_spacing)
        layout.addWidget(self.grid_spin)

        layout.addWidget(self._separator())

        self.aspect_cb = QCheckBox("Lock aspect")
        self.aspect_cb.toggled.connect(self._on_aspect_toggled)
        layout.addWidget(self.aspect_cb)
        self.aspect_combo = QComboBox()
        for ratio in ASPECT_CHOICES:
            self.aspect_combo.addItem(ratio, ratio)
        self.aspect_combo.currentIndexChanged.connect(self._on_aspect_combo)
        layout.addWidget(self.aspect_combo)

        layout.addStretch(1)
        return ribbon

    def _build_sidebar(self) -> QFrame:
        side = QFrame()
        side.setObjectName("sidebar")
        side.setMinimumWidth(180)
        side.setMaximumWidth(360)
        layout = QVBoxLayout(side)
        layout.setContentsMargins(8, 8, 8, 8)
        header = QHBoxLayout()
        self.sidebar_title = QLabel("Files")
        self.sidebar_title.setObjectName("sidebarTitle")
        header.addWidget(self.sidebar_title, 1)
        refresh = QPushButton("Refresh")
        refresh.setFixedWidth(72)
        refresh.clicked.connect(self.refresh_list)
        header.addWidget(refresh)
        layout.addLayout(header)
        self.file_list = QListWidget()
        self.file_list.currentRowChanged.connect(self._on_file_row)
        layout.addWidget(self.file_list, 1)
        return side

    def _separator(self) -> QFrame:
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setStyleSheet("color: #3e3e42; max-width: 1px;")
        return line

    def _bind_shortcuts(self) -> None:
        QShortcut(QKeySequence.Save, self, self.save_crop)
        QShortcut(QKeySequence(Qt.Key_Return), self, self.save_crop)
        QShortcut(QKeySequence(Qt.Key_Enter), self, self.save_crop)
        QShortcut(QKeySequence(Qt.Key_Escape), self, self.canvas.clear_selection)
        QShortcut(QKeySequence.Copy, self, self.copy_to_clipboard)
        QShortcut(QKeySequence("Ctrl+Left"), self, lambda: self.rotate(False))
        QShortcut(QKeySequence("Ctrl+Right"), self, lambda: self.rotate(True))

    def _apply_settings_to_widgets(self) -> None:
        self.grid_cb.blockSignals(True)
        self.aspect_cb.blockSignals(True)
        self.grid_spin.blockSignals(True)
        self.aspect_combo.blockSignals(True)
        self.zoom_combo.blockSignals(True)
        self.resize_combo.blockSignals(True)

        self.grid_cb.setChecked(self.settings.grid_enabled)
        self.grid_spin.setValue(self.settings.grid_spacing)
        self.aspect_cb.setChecked(self.settings.aspect_enabled)
        idx = self.aspect_combo.findData(self.settings.aspect_ratio)
        self.aspect_combo.setCurrentIndex(max(0, idx))
        zidx = self.zoom_combo.findData(self.settings.zoom_mode)
        self.zoom_combo.setCurrentIndex(max(0, zidx))
        ridx = self.resize_combo.findData(self.settings.resize_long_side)
        self.resize_combo.setCurrentIndex(max(0, ridx) if self.settings.auto_resize else 0)

        self.grid_cb.blockSignals(False)
        self.aspect_cb.blockSignals(False)
        self.grid_spin.blockSignals(False)
        self.aspect_combo.blockSignals(False)
        self.zoom_combo.blockSignals(False)
        self.resize_combo.blockSignals(False)

        self.canvas.set_auto_save(self.settings.auto_save)
        self.canvas.set_grid(self.settings.grid_enabled, self.settings.grid_spacing)
        self.canvas.set_aspect(self.settings.aspect_enabled, self.settings.aspect_ratio)

    def open_dialog(self) -> None:
        start = self.settings.last_dir or QStandardPaths.writableLocation(QStandardPaths.PicturesLocation)
        path, _ = QFileDialog.getOpenFileName(self, "Open image", start, OPEN_FILTER)
        if path:
            self.open_path(Path(path))

    def open_path(self, path: Path, populate_list: bool | None = None) -> None:
        path = Path(path).expanduser().resolve()
        if not path.exists():
            QMessageBox.warning(self, APP_NAME, f"File not found:\n{path}")
            return
        if populate_list is None:
            populate_list = self.path is None
        try:
            source = load_image(path)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.warning(self, APP_NAME, f"Could not open image:\n{exc}")
            return
        self.path = path
        self.source = source
        self.rotation = 0
        if self.settings.auto_resize:
            self.long_side = self.settings.resize_long_side
        else:
            self.long_side = None
        self._sync_resize_combo()
        self._refresh_working()
        if populate_list:
            self.folder_files = list_images(path.parent)
            self._fill_sidebar()
        else:
            self._sync_sidebar_current()
        self.settings.last_dir = str(path.parent)
        save_settings(self.settings)
        self.msg_label.setText(path.name)

    def _refresh_working(self) -> None:
        if self.source is None:
            return
        self.working = render_working(
            self.source,
            rotation=self.rotation,
            long_side=self.long_side,
            dont_upscale=self.settings.dont_upscale,
        )
        self.canvas.set_pixmap(pil_to_qpixmap(self.working))
        self.canvas.set_zoom_mode(self.canvas.zoom_mode())
        self._update_title()
        self._update_status()

    def rotate(self, clockwise: bool) -> None:
        if self.source is None:
            return
        self.rotation = (self.rotation + (90 if clockwise else -90)) % 360
        self._refresh_working()

    def save_crop(self) -> None:
        if self.working is None or self.path is None:
            return
        box = self.canvas.selection_box()
        if box is None:
            return
        try:
            cropped = crop_image(self.working, box)
        except ValueError:
            return
        ext = effective_ext(self.path, self.settings.output_format)
        dest = next_dest_path(
            self.path,
            preset=self.settings.naming_preset,
            digits=self.settings.seq_digits,
            subfolder=self.settings.subfolder,
            ext=ext,
        )
        try:
            save_image(cropped, dest, jpeg_quality=self.settings.jpeg_quality)
        except OSError as exc:
            QMessageBox.warning(self, APP_NAME, f"Could not save:\n{exc}")
            return
        self.msg_label.setText(f"Saved: {dest.name}")
        self.canvas.clear_selection()

    def copy_to_clipboard(self) -> None:
        if self.working is None:
            return
        box = self.canvas.selection_box()
        image = crop_image(self.working, box) if box else self.working
        QApplication.clipboard().setPixmap(pil_to_qpixmap(image))
        self.msg_label.setText("Copied to clipboard")

    def step_file(self, delta: int) -> None:
        row = self.file_list.currentRow()
        new_row = row + delta
        if 0 <= new_row < self.file_list.count():
            self.file_list.setCurrentRow(new_row)

    def refresh_list(self) -> None:
        if self.path is None:
            return
        self.folder_files = list_images(self.path.parent)
        self._fill_sidebar()

    def open_current_folder(self) -> None:
        folder = self.path.parent if self.path else Path(self.settings.last_dir or ".")
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(folder)))

    def open_settings(self) -> None:
        sample = self.path.name if self.path else "IMG_1234.jpg"
        dialog = SettingsDialog(self.settings, sample, self)
        if dialog.exec():
            dialog.apply_to(self.settings)
            save_settings(self.settings)
            self.canvas.set_auto_save(self.settings.auto_save)
            if self.settings.auto_save:
                self.canvas.save_btn.hide()

    def show_about(self) -> None:
        QMessageBox.about(
            self,
            APP_NAME,
            f"{APP_NAME} {__version__}\n\n"
            "Open an image, select a region, save a crop under a new name.",
        )

    def _fill_sidebar(self) -> None:
        self.file_list.blockSignals(True)
        self.file_list.clear()
        for path in self.folder_files:
            item = QListWidgetItem(path.name)
            item.setData(Qt.UserRole, str(path))
            item.setToolTip(str(path))
            self.file_list.addItem(item)
        self.file_list.blockSignals(False)
        self.sidebar_title.setText(f"Files ({len(self.folder_files)})")
        self._sync_sidebar_current()

    def _sync_sidebar_current(self) -> None:
        if self.path is None:
            return
        self.file_list.blockSignals(True)
        current = str(self.path)
        for i in range(self.file_list.count()):
            if self.file_list.item(i).data(Qt.UserRole) == current:
                self.file_list.setCurrentRow(i)
                break
        self.file_list.blockSignals(False)

    def _sync_resize_combo(self) -> None:
        self.resize_combo.blockSignals(True)
        target = self.long_side or 0
        idx = self.resize_combo.findData(target)
        self.resize_combo.setCurrentIndex(max(0, idx))
        self.resize_combo.blockSignals(False)

    def _on_file_row(self, row: int) -> None:
        if row < 0:
            return
        item = self.file_list.item(row)
        path = Path(str(item.data(Qt.UserRole)))
        if self.path is not None and path.resolve() == self.path.resolve():
            return
        self.open_path(path, populate_list=False)

    def _on_zoom_combo(self) -> None:
        mode = str(self.zoom_combo.currentData())
        self.settings.zoom_mode = mode
        self.canvas.set_zoom_mode(mode)
        save_settings(self.settings)

    def _on_resize_combo(self) -> None:
        value = int(self.resize_combo.currentData() or 0)
        if value:
            self.settings.resize_long_side = value
            self.long_side = value
            save_settings(self.settings)
        else:
            self.long_side = None
        if self.source is not None:
            self._refresh_working()

    def _on_grid_toggled(self, checked: bool) -> None:
        if checked and self.aspect_cb.isChecked():
            self.aspect_cb.blockSignals(True)
            self.aspect_cb.setChecked(False)
            self.aspect_cb.blockSignals(False)
            self.settings.aspect_enabled = False
        self.settings.grid_enabled = checked
        self.canvas.set_grid(checked, self.settings.grid_spacing)
        self.canvas.set_aspect(self.settings.aspect_enabled, self.settings.aspect_ratio)
        save_settings(self.settings)

    def _on_aspect_toggled(self, checked: bool) -> None:
        if checked and self.grid_cb.isChecked():
            self.grid_cb.blockSignals(True)
            self.grid_cb.setChecked(False)
            self.grid_cb.blockSignals(False)
            self.settings.grid_enabled = False
        self.settings.aspect_enabled = checked
        self.canvas.set_grid(self.settings.grid_enabled, self.settings.grid_spacing)
        self.canvas.set_aspect(checked, self.settings.aspect_ratio)
        save_settings(self.settings)

    def _on_grid_spacing(self, value: int) -> None:
        self.settings.grid_spacing = value
        self.canvas.set_grid(self.settings.grid_enabled, value)
        save_settings(self.settings)

    def _on_aspect_combo(self) -> None:
        ratio = str(self.aspect_combo.currentData())
        self.settings.aspect_ratio = ratio
        self.canvas.set_aspect(self.settings.aspect_enabled, ratio)
        save_settings(self.settings)

    def _on_cursor(self, x: int, y: int) -> None:
        if self.working is None:
            self.coord_label.setText("Pos: —")
            return
        if 0 <= x < self.working.width and 0 <= y < self.working.height:
            self.coord_label.setText(f"Pos: {x}, {y}")
        else:
            self.coord_label.setText("Pos: —")

    def _on_selection(self, box: object) -> None:
        if not box:
            self.sel_label.setText("Sel: —")
            return
        left, top, right, bottom = box  # type: ignore[misc]
        self.sel_label.setText(f"Sel: {right - left} x {bottom - top}")

    def _on_zoom_changed(self, _mode: str, value: float) -> None:
        self.zoom_label.setText(f"Zoom: {value * 100:.0f}%")

    def _update_title(self) -> None:
        if self.path is None or self.working is None:
            self.setWindowTitle(APP_NAME)
            return
        self.setWindowTitle(
            f"{APP_NAME} - {self.path.name} ({self.working.width}x{self.working.height})"
        )

    def _update_status(self) -> None:
        if self.working is None:
            self.img_label.setText("Image: —")
            self.zoom_label.setText("Zoom: —")
            return
        self.img_label.setText(f"Image: {self.working.width} x {self.working.height}")
        self.zoom_label.setText(f"Zoom: {self.canvas.zoom_value() * 100:.0f}%")

    def dragEnterEvent(self, event) -> None:  # noqa: ANN001
        if first_dropped_image(event.mimeData()) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event) -> None:  # noqa: ANN001
        if first_dropped_image(event.mimeData()) is not None:
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event) -> None:  # noqa: ANN001
        path = first_dropped_image(event.mimeData())
        if path is None:
            event.ignore()
            return
        self.open_path(path)
        event.acceptProposedAction()

    def closeEvent(self, event) -> None:  # noqa: ANN001
        geo = self.geometry()
        self.settings.window_x = geo.x()
        self.settings.window_y = geo.y()
        self.settings.window_w = geo.width()
        self.settings.window_h = geo.height()
        self.settings.splitter = self.splitter.sizes()
        save_settings(self.settings)
        super().closeEvent(event)


def main() -> None:
    QLocale.setDefault(QLocale(QLocale.English, QLocale.UnitedStates))
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(ORG_NAME)
    app.setWindowIcon(make_app_icon())
    apply_theme(app)
    window = MainWindow()
    window.show()
    paths = [Path(arg) for arg in sys.argv[1:] if not arg.startswith("-")]
    for path in paths:
        if is_image_file(path):
            window.open_path(path)
            break
    sys.exit(app.exec())
