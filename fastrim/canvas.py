from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, QRectF, QSize, Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QPixmap, QWheelEvent
from PySide6.QtWidgets import (
    QFrame,
    QGraphicsObject,
    QGraphicsPixmapItem,
    QGraphicsRectItem,
    QGraphicsScene,
    QGraphicsView,
    QLabel,
    QPushButton,
)

from fastrim.geom import box_size, parse_aspect, selection_from_drag


class GridItem(QGraphicsObject):
    def __init__(self) -> None:
        super().__init__()
        self._width = 0
        self._height = 0
        self._spacing = 16
        self.setZValue(5)
        self.setAcceptedMouseButtons(Qt.NoButton)

    def set_geometry(self, width: int, height: int, spacing: int) -> None:
        self.prepareGeometryChange()
        self._width = width
        self._height = height
        self._spacing = max(2, spacing)
        self.update()

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, self._width, self._height)

    def paint(self, painter: QPainter, option, widget=None) -> None:  # noqa: ANN001
        if self._width <= 0 or self._height <= 0 or self._spacing <= 0:
            return
        scale = painter.worldTransform().m11()
        if scale * self._spacing < 4:
            return
        painter.setPen(QPen(QColor(0, 220, 90, 80), 0))
        exposed = option.exposedRect.adjusted(-1, -1, 1, 1)
        start_x = max(0, int(exposed.left()) // self._spacing * self._spacing)
        start_y = max(0, int(exposed.top()) // self._spacing * self._spacing)
        end_x = min(self._width, int(exposed.right()) + 1)
        end_y = min(self._height, int(exposed.bottom()) + 1)
        x = start_x
        while x <= end_x:
            painter.drawLine(x, 0, x, self._height)
            x += self._spacing
        y = start_y
        while y <= end_y:
            painter.drawLine(0, y, self._width, y)
            y += self._spacing


class ImageCanvas(QGraphicsView):
    cursorMoved = Signal(int, int)
    selectionChanged = Signal(object)
    cropSaveRequested = Signal()
    zoomChanged = Signal(str, float)
    openRequested = Signal()

    def __init__(self, parent=None) -> None:  # noqa: ANN001
        super().__init__(parent)
        self._scene = QGraphicsScene(self)
        self.setScene(self._scene)
        self.setFrameShape(QFrame.NoFrame)
        self.setBackgroundBrush(QColor("#121212"))
        self.setMouseTracking(True)
        self.setDragMode(QGraphicsView.NoDrag)
        self.setViewportUpdateMode(QGraphicsView.SmartViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.NoAnchor)
        self.setResizeAnchor(QGraphicsView.NoAnchor)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setRenderHints(QPainter.Antialiasing | QPainter.SmoothPixmapTransform)

        self._pix_item: QGraphicsPixmapItem | None = None
        self._grid = GridItem()
        self._scene.addItem(self._grid)
        self._grid.hide()
        self._sel_item = QGraphicsRectItem()
        self._sel_item.setZValue(10)
        self._sel_item.setPen(QPen(QColor("#7bd4ff"), 0, Qt.DashLine))
        self._sel_item.setBrush(QColor(80, 180, 255, 40))
        self._sel_item.hide()
        self._scene.addItem(self._sel_item)

        self._img_w = 0
        self._img_h = 0
        self._zoom = 1.0
        self._zoom_mode = "fit"
        self._grid_enabled = False
        self._grid_spacing = 16
        self._aspect_enabled = False
        self._aspect_ratio = "16:9"
        self._auto_save = False

        self._selecting = False
        self._origin = QPointF()
        self._box: tuple[int, int, int, int] | None = None
        self._panning = False
        self._pan_start = QPoint()

        self._empty = QLabel("Open an image (Ctrl+O) or drop one here", self.viewport())
        self._empty.setAlignment(Qt.AlignCenter)
        self._empty.setStyleSheet("color: #8a8a8a; font-size: 16px; background: transparent;")
        self._empty.setAttribute(Qt.WA_TransparentForMouseEvents)

        self.save_btn = QPushButton("Save", self.viewport())
        self.save_btn.setObjectName("cropSaveBtn")
        self.save_btn.setCursor(Qt.PointingHandCursor)
        self.save_btn.setStyleSheet(
            "QPushButton#cropSaveBtn { background:#2ea043; color:#fff; border:none;"
            " border-radius:4px; padding:4px 12px; font-weight:700; }"
            "QPushButton#cropSaveBtn:hover { background:#3fb950; }"
        )
        self.save_btn.hide()
        self.save_btn.clicked.connect(self.cropSaveRequested.emit)

    def has_image(self) -> bool:
        return self._pix_item is not None

    def image_size(self) -> QSize:
        return QSize(self._img_w, self._img_h)

    def zoom_mode(self) -> str:
        return self._zoom_mode

    def zoom_value(self) -> float:
        return self._zoom

    def selection_box(self) -> tuple[int, int, int, int] | None:
        return self._box

    def set_auto_save(self, enabled: bool) -> None:
        self._auto_save = enabled
        if enabled:
            self.save_btn.hide()

    def set_grid(self, enabled: bool, spacing: int) -> None:
        self._grid_enabled = enabled
        self._grid_spacing = max(2, spacing)
        self._grid.set_geometry(self._img_w, self._img_h, self._grid_spacing)
        self._grid.setVisible(enabled and self._pix_item is not None)

    def set_aspect(self, enabled: bool, ratio: str) -> None:
        self._aspect_enabled = enabled
        self._aspect_ratio = ratio

    def set_pixmap(self, pixmap: QPixmap) -> None:
        self.clear_selection()
        if self._pix_item is not None:
            self._scene.removeItem(self._pix_item)
            self._pix_item = None
        self._pix_item = self._scene.addPixmap(pixmap)
        self._pix_item.setZValue(0)
        self._img_w = pixmap.width()
        self._img_h = pixmap.height()
        self._scene.setSceneRect(0, 0, self._img_w, self._img_h)
        self._grid.set_geometry(self._img_w, self._img_h, self._grid_spacing)
        self._grid.setVisible(self._grid_enabled)
        self._empty.hide()
        if self._zoom_mode == "fit":
            self._fit()
        else:
            self._apply_absolute_zoom(self._zoom)

    def clear_image(self) -> None:
        self.clear_selection()
        if self._pix_item is not None:
            self._scene.removeItem(self._pix_item)
            self._pix_item = None
        self._img_w = 0
        self._img_h = 0
        self._grid.hide()
        self._empty.show()
        self._empty.raise_()
        self.resetTransform()
        self._zoom = 1.0

    def clear_selection(self) -> None:
        self._selecting = False
        self._box = None
        self._sel_item.hide()
        self.save_btn.hide()
        self.selectionChanged.emit(None)

    def set_selection_box(self, box: tuple[int, int, int, int] | None) -> None:
        if box is None:
            self.clear_selection()
            return
        width, height = box_size(box)
        if width < 1 or height < 1:
            self.clear_selection()
            return
        self._box = box
        left, top, right, bottom = box
        self._sel_item.setRect(QRectF(left, top, right - left, bottom - top))
        self._sel_item.show()
        if not self._auto_save:
            self.save_btn.show()
            self.save_btn.raise_()
            self._reposition_save_btn()
        self.selectionChanged.emit(box)

    def set_zoom_mode(self, mode: str) -> None:
        self._zoom_mode = mode
        if self._pix_item is None:
            return
        if mode == "fit":
            self._fit()
            return
        try:
            percent = float(mode)
        except ValueError:
            return
        self._apply_absolute_zoom(percent / 100.0)

    def resizeEvent(self, event) -> None:  # noqa: ANN001
        super().resizeEvent(event)
        self._empty.setGeometry(self.viewport().rect())
        if self._zoom_mode == "fit" and self._pix_item is not None:
            self._fit()
        self._reposition_save_btn()

    def showEvent(self, event) -> None:  # noqa: ANN001
        super().showEvent(event)
        if self._zoom_mode == "fit" and self._pix_item is not None:
            self._fit()

    def scrollContentsBy(self, dx: int, dy: int) -> None:
        super().scrollContentsBy(dx, dy)
        self._reposition_save_btn()

    def mousePressEvent(self, event) -> None:  # noqa: ANN001
        if self._pix_item is None:
            if event.button() == Qt.LeftButton:
                self.openRequested.emit()
            return
        if event.button() == Qt.MiddleButton or (
            event.button() == Qt.LeftButton and event.modifiers() & Qt.ControlModifier
        ):
            self._panning = True
            self._pan_start = event.position().toPoint()
            self.setCursor(Qt.ClosedHandCursor)
            event.accept()
            return
        if event.button() == Qt.LeftButton:
            scene_pos = self.mapToScene(event.position().toPoint())
            if not self._in_image(scene_pos):
                return
            self._selecting = True
            self._origin = QPointF(
                min(max(scene_pos.x(), 0), self._img_w),
                min(max(scene_pos.y(), 0), self._img_h),
            )
            self.save_btn.hide()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event) -> None:  # noqa: ANN001
        pos = event.position().toPoint()
        scene_pos = self.mapToScene(pos)
        self.cursorMoved.emit(int(scene_pos.x()), int(scene_pos.y()))
        if self._panning:
            delta = pos - self._pan_start
            self._pan_start = pos
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() - delta.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() - delta.y())
            event.accept()
            return
        if self._selecting:
            box = self._box_from_points(self._origin, scene_pos)
            self._preview_box(box)
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event) -> None:  # noqa: ANN001
        if self._panning and event.button() in (Qt.MiddleButton, Qt.LeftButton):
            self._panning = False
            self.unsetCursor()
            event.accept()
            return
        if self._selecting and event.button() == Qt.LeftButton:
            self._selecting = False
            scene_pos = self.mapToScene(event.position().toPoint())
            box = self._box_from_points(self._origin, scene_pos)
            width, height = box_size(box)
            if width < 2 or height < 2:
                self.clear_selection()
                event.accept()
                return
            self.set_selection_box(box)
            if self._auto_save:
                self.cropSaveRequested.emit()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def wheelEvent(self, event: QWheelEvent) -> None:
        if self._pix_item is None:
            return
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        new_zoom = min(16.0, max(0.05, self._zoom * factor))
        self._zoom_at(new_zoom, event.position().toPoint())
        event.accept()

    def _in_image(self, scene_pos: QPointF) -> bool:
        return 0 <= scene_pos.x() < self._img_w and 0 <= scene_pos.y() < self._img_h

    def _constraints(self) -> tuple[tuple[int, int] | None, int | None]:
        aspect = parse_aspect(self._aspect_ratio) if self._aspect_enabled else None
        grid = self._grid_spacing if self._grid_enabled and not self._aspect_enabled else None
        return aspect, grid

    def _box_from_points(self, origin: QPointF, current: QPointF) -> tuple[int, int, int, int]:
        aspect, grid = self._constraints()
        return selection_from_drag(
            origin.x(),
            origin.y(),
            current.x(),
            current.y(),
            self._img_w,
            self._img_h,
            aspect=aspect,
            grid=grid,
        )

    def _preview_box(self, box: tuple[int, int, int, int]) -> None:
        width, height = box_size(box)
        if width < 1 or height < 1:
            self._sel_item.hide()
            return
        left, top, right, bottom = box
        self._sel_item.setRect(QRectF(left, top, right - left, bottom - top))
        self._sel_item.show()

    def _fit(self) -> None:
        if self._pix_item is None:
            return
        self._zoom_mode = "fit"
        self.resetTransform()
        self.fitInView(self._pix_item, Qt.KeepAspectRatio)
        self._zoom = self.transform().m11() or 1.0
        self.zoomChanged.emit("fit", self._zoom)
        self._reposition_save_btn()

    def _apply_absolute_zoom(self, zoom: float) -> None:
        self._zoom_mode = "custom"
        self._zoom = zoom
        self.resetTransform()
        self.scale(zoom, zoom)
        self.zoomChanged.emit("custom", self._zoom)
        self._reposition_save_btn()

    def _zoom_at(self, new_zoom: float, view_pos: QPoint) -> None:
        old_scene = self.mapToScene(view_pos)
        self._zoom_mode = "custom"
        self.resetTransform()
        self.scale(new_zoom, new_zoom)
        self._zoom = new_zoom
        new_view = self.mapFromScene(old_scene)
        delta = new_view - view_pos
        self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + delta.x())
        self.verticalScrollBar().setValue(self.verticalScrollBar().value() + delta.y())
        self.zoomChanged.emit("custom", self._zoom)
        self._reposition_save_btn()

    def _reposition_save_btn(self) -> None:
        if self._box is None or self.save_btn.isHidden():
            return
        left, top, right, bottom = self._box
        view_pt = self.mapFromScene(QPointF(right, bottom))
        x = view_pt.x() + 6
        y = view_pt.y() + 6
        vw = self.viewport().width()
        vh = self.viewport().height()
        bw = self.save_btn.sizeHint().width()
        bh = self.save_btn.sizeHint().height()
        if x + bw > vw - 4:
            x = max(4, view_pt.x() - bw - 6)
        if y + bh > vh - 4:
            y = max(4, view_pt.y() - bh - 6)
        x = max(4, min(x, vw - bw - 4))
        y = max(4, min(y, vh - bh - 4))
        self.save_btn.move(x, y)
        self.save_btn.resize(bw, bh)
