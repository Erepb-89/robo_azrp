"""Карта точек и связей манипулятора для инженерного окна."""

import math

from PyQt5.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt5.QtGui import QBrush, QColor, QFont, QPainter, QPainterPath, QPen
from PyQt5.QtWidgets import (
    QGraphicsEllipseItem,
    QGraphicsPathItem,
    QGraphicsScene,
    QGraphicsSimpleTextItem,
    QGraphicsView,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

# Фон, контур, маркер и текст узла.
NODE_STYLES = {
    "base": ("#ffffff", "#a7b8cc", "#7187a0", "#17202b"),
    "major": ("#ecf2f9", "#8fa4bd", "#496581", "#17202b"),
    "endpoint": ("#eef4ff", "#a9c3ff", "#638df0", "#17202b"),
    "home": ("#0b5cff", "#0b5cff", "#ffffff", "#ffffff"),
    "current": ("#e1f5e9", "#0c8a42", "#0c8a42", "#07542a"),
    "blocked": ("#fdecec", "#c62828", "#c62828", "#8a1717"),
}

ZONE_STYLES = {
    "Device1": ("#f6f8fb", "#d3dbe4"),
    "Table": ("#eef4ff", "#c7d8f5"),
    "Device2": ("#f6f8fb", "#d3dbe4"),
}

PEN_NORMAL = QPen(QColor("#859ab2"), 2)
PEN_REVERSE = QPen(QColor("#9aadc2"), 2)
PEN_HIGHLIGHT = QPen(QColor("#0b5cff"), 3.4)
PEN_DIM = QPen(QColor("#d6e0eb"), 1.6)
MAP_PROMPT = "Выберите точку, чтобы увидеть её название"


def map_font(pixel_size, bold=False):
    font = QFont()
    font.setFamilies(["Segoe UI", "Noto Sans", "Arial", font.family()])
    font.setPixelSize(pixel_size)
    font.setBold(bold)
    return font


class NodeItem(QGraphicsPathItem):
    def __init__(self, point_name, display_name, position, kind, on_click):
        super().__init__()
        self.point_name = point_name
        self.display_name = display_name
        self.kind = kind
        self.on_click = on_click
        self._is_current = False
        self._is_blocked = False
        self._is_selected = False
        self._is_hovered = False

        self.label = QGraphicsSimpleTextItem(display_name, self)
        self.label.setFont(map_font(17, bold=True))
        self.label.setAcceptedMouseButtons(Qt.NoButton)
        label_rect = self.label.boundingRect()
        width = label_rect.width() + 34
        self.shape_rect = QRectF(-width / 2, -18, width, 36)
        self.label.setPos(self.shape_rect.left() + 24, -label_rect.height() / 2)

        shape = QPainterPath()
        shape.addRoundedRect(self.shape_rect, 12, 12)
        self.setPath(shape)
        self.marker = QGraphicsEllipseItem(self.shape_rect.left() + 8, -4, 8, 8, self)
        self.marker.setPen(QPen(Qt.NoPen))
        self.marker.setAcceptedMouseButtons(Qt.NoButton)

        self.setPos(position)
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setToolTip(point_name)
        self._update_style()

    def hoverEnterEvent(self, event):
        self._is_hovered = True
        self._update_style()
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self._is_hovered = False
        self._update_style()
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.on_click(self.point_name)
            event.accept()
        else:
            super().mousePressEvent(event)

    def set_selected(self, selected):
        self._is_selected = selected
        self._update_style()

    def set_current(self, is_current):
        self._is_current = is_current
        self._update_style()

    def set_blocked(self, blocked, reason=""):
        self._is_blocked = blocked
        self.setToolTip(f"{self.point_name}\nЗона недоступна: {reason}" if blocked and reason else self.point_name)
        self._update_style()

    def _update_style(self):
        kind = self.kind
        if self._is_current:
            kind = "current"
        if self._is_blocked:
            kind = "blocked"
        background, outline, marker, text = NODE_STYLES[kind]
        emphasized = self._is_selected or self._is_hovered or self._is_current
        if emphasized and kind in ("base", "major", "endpoint"):
            outline = "#0b5cff"
        if emphasized and kind == "home":
            outline = "#09399b"
        self.setBrush(QBrush(QColor(background)))
        pen = QPen(QColor(outline), 3 if emphasized else 1.6)
        if self._is_blocked:
            pen.setStyle(Qt.DashLine)
        self.setPen(pen)
        self.marker.setBrush(QBrush(QColor(marker)))
        self.label.setBrush(QBrush(QColor(text)))


def edge_point(node, direction):
    """Точка на границе карточки по направлению к соседнему узлу."""
    half_width = node.shape_rect.width() / 2
    half_height = node.shape_rect.height() / 2
    dx, dy = abs(direction.x()), abs(direction.y())
    distance = min(half_width / dx if dx else math.inf, half_height / dy if dy else math.inf)
    return node.pos() + direction * (distance + 4)


def add_arrowhead(path, tip, direction, size):
    normal = QPointF(-direction.y(), direction.x())
    base = tip - direction * size
    path.moveTo(base + normal * (size * 0.5))
    path.lineTo(tip)
    path.lineTo(base - normal * (size * 0.5))


class TrajectoryView(QGraphicsView):
    def __init__(self, scene, parent):
        super().__init__(scene, parent)
        self.setObjectName("trajectoryView")
        self.setRenderHint(QPainter.Antialiasing)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
        self._zoom = 1.0

    def fit_map(self):
        if self.sceneRect().isEmpty():
            return
        self._zoom = 1.0
        self.resetTransform()
        self.fitInView(self.sceneRect(), Qt.KeepAspectRatio)

    def zoom_by(self, factor):
        scale = min(4.0, max(1.0, self._zoom * factor))
        if scale == 1.0:
            self.fit_map()
            return
        factor = scale / self._zoom
        self.scale(factor, factor)
        self._zoom = scale

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta:
            self.zoom_by(1.18 ** (delta / 120))
            event.accept()
        else:
            super().wheelEvent(event)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self._zoom == 1.0:
            self.fit_map()


class TrajectoryMapWidget(QWidget):
    """Показывает точки, состояние карты и выделенное ребро маршрута."""

    node_clicked = pyqtSignal(str)

    NODE_LAYOUT = {  # node_x, node_y, display, is_endpoint, is_major
        "BGIntP010": (510, 930, "BGIntP010", False, False),  # Home – основная
        "BGIntP011": (510, 1030, "BGIntP011", True, False),
        "BGIntP001": (510, 830, "BGIntP001", True, True),
        "BG1IntP010": (410, 710, "BG1IntP010", True, False),
        "BG2IntP010": (610, 710, "BG2IntP010", True, False),

        "BGM1P010": (410, 930, "BGM1P010", False, False),
        "BGM1P015": (360, 1030, "BGM1P015", False, False),
        "BGM1P020": (330, 930, "BGM1P020", False, True),
        "BAM1P010": (260, 800, "BAM1P010", False, False),
        "BAM1P015": (260, 710, "BAM1P015", False, True),
        "EAM1P000": (160, 710, "EAM1P000", False, False),
        "EAM1P010": (160, 620, "EAM1P010", True, False),
        "EAM1P020": (65, 710, "EAM1P020", True, False),
        "EAM1P030": (65, 800, "EAM1P030", True, False),
        "EAM1P040": (160, 800, "EAM1P040", True, False),
        "BG2M1P010": (260, 930, "BG2M1P010", False, True),
        "EG2M1P010": (160, 930, "EG2M1P010", False, False),
        "EG2M1P020": (160, 1030, "EG2M1P020", True, False),
        "BG1M1P010": (260, 1130, "BG1M1P010", False, True),
        "EG1M1P010": (160, 1130, "EG1M1P010", False, False),
        "EG1M1P020": (160, 1190, "EG1M1P020", False, False),
        "EG1M1P030": (160, 1250, "EG1M1P030", False, False),
        "EG1M1P040": (65, 1190, "EG1M1P040", True, False),

        "BGM2P010": (610, 930, "BGM2P010", False, False),
        "BGM2P015": (660, 1030, "BGM2P015", False, False),
        "BGM2P020": (690, 930, "BGM2P020", False, True),
        "BAM2P010": (760, 800, "BAM2P010", False, False),
        "BAM2P015": (760, 710, "BAM2P015", False, True),
        "EAM2P000": (860, 710, "EAM2P000", False, False),
        "EAM2P010": (860, 620, "EAM2P010", True, False),
        "EAM2P020": (955, 710, "EAM2P020", True, False),
        "EAM2P030": (955, 800, "EAM2P030", True, False),
        "EAM2P040": (860, 800, "EAM2P040", True, False),
        "BG2M2P010": (760, 930, "BG2M2P010", False, True),
        "EG2M2P010": (860, 930, "EG2M2P010", False, False),
        "EG2M2P020": (860, 1030, "EG2M2P020", True, False),
        "BG1M2P010": (760, 1130, "BG1M2P010", False, True),
        "EG1M2P010": (860, 1130, "EG1M2P010", False, False),
        "EG1M2P020": (860, 1190, "EG1M2P020", False, False),
        "EG1M2P030": (860, 1250, "EG1M2P030", False, False),
        "EG1M2P040": (955, 1190, "EG1M2P040", True, False),
    }

    EDGES = [
        # От Home
        ("BGIntP010", "BGIntP011"),
        ("BGIntP010", "BGM1P010"),
        ("BGIntP010", "BG1IntP010"),
        ("BGIntP010", "BG2IntP010"),
        ("BGIntP010", "BGIntP001"),
        ("BGM1P010", "BGM1P015"),
        ("BGM1P015", "BGM1P020"),
        ("BGM1P020", "BAM1P010"),

        ("BAM1P010", "BAM1P015"),
        ("BAM1P015", "EAM1P000"),
        ("EAM1P000", "EAM1P010"),
        ("EAM1P000", "EAM1P020"),
        ("EAM1P000", "EAM1P030"),
        ("EAM1P000", "EAM1P040"),

        ("BGM1P020", "BG2M1P010"),
        ("BG2M1P010", "EG2M1P010"),
        ("EG2M1P010", "EG2M1P020"),

        ("BGM1P020", "BG1M1P010"),
        ("BG1M1P010", "EG1M1P010"),
        ("EG1M1P010", "EG1M1P020"),
        ("EG1M1P020", "EG1M1P030"),
        ("EG1M1P030", "EG1M1P040"),
        ("EG1M1P040", "EG1M1P010"),

        ("BGIntP010", "BGM2P010"),
        ("BGM2P010", "BGM2P015"),
        ("BGM2P015", "BGM2P020"),
        ("BGM2P020", "BAM2P010"),

        ("BAM2P010", "BAM2P015"),
        ("BAM2P015", "EAM2P000"),
        ("EAM2P000", "EAM2P010"),
        ("EAM2P000", "EAM2P020"),
        ("EAM2P000", "EAM2P030"),
        ("EAM2P000", "EAM2P040"),

        ("BGM2P020", "BG2M2P010"),
        ("BG2M2P010", "EG2M2P010"),
        ("EG2M2P010", "EG2M2P020"),

        ("BGM2P020", "BG1M2P010"),
        ("BG1M2P010", "EG1M2P010"),
        ("EG1M2P010", "EG1M2P020"),
        ("EG1M2P020", "EG1M2P030"),
        ("EG1M2P030", "EG1M2P040"),
        ("EG1M2P040", "EG1M2P010"),
    ]

    ZONES = [
        (20, 550, 200, 750, "Device1", "Станок 1"),
        (370, 550, 280, 330, "Table", "Стол"),
        (800, 550, 200, 750, "Device2", "Станок 2"),
    ]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("trajectoryMap")
        self._current_point = None
        self._selected_point = None
        self._nodes = {}
        self._edge_items = {}

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)
        layout.addLayout(self._make_toolbar())

        self._scene = QGraphicsScene(self)
        self._view = TrajectoryView(self._scene, self)
        layout.addWidget(self._view, 1)

        self._info_label = QLabel(MAP_PROMPT)
        self._info_label.setObjectName("trajectoryMapStatus")
        layout.addWidget(self._info_label)

        self._build_scene()
        self.node_clicked.connect(self._on_node_clicked)

    def _make_toolbar(self):
        toolbar = QHBoxLayout()
        toolbar.setSpacing(8)
        for text, kind in (
            ("Исходная", "home"),
            ("Базовая", "base"),
            ("Конечная", "endpoint"),
            ("Недоступна", "blocked"),
            ("Текущая", "current"),
        ):
            dot = QLabel()
            dot.setFixedSize(12, 12)
            color = NODE_STYLES[kind][0 if kind == "home" else 2]
            dot.setStyleSheet(f"background-color: {color}; border-radius: 6px;")
            label = QLabel(text)
            label.setObjectName("trajectoryMapLegend")
            toolbar.addWidget(dot, 0, Qt.AlignVCenter)
            toolbar.addWidget(label)
            toolbar.addSpacing(16)

        toolbar.addStretch()
        for text, tooltip, action in (
            ("−", "Уменьшить масштаб", lambda: self._view.zoom_by(1 / 1.18)),
            ("+", "Увеличить масштаб", lambda: self._view.zoom_by(1.18)),
            ("Вся карта", "Показать все точки", lambda: self._view.fit_map()),
        ):
            button = QPushButton(text)
            button.setToolTip(tooltip)
            button.setAccessibleName(tooltip)
            button.clicked.connect(action)
            toolbar.addWidget(button)
        return toolbar

    def _build_scene(self):
        horizontal_scale = 2.15
        for x, y, width, height, kind, text in self.ZONES:
            rect = QRectF(x * horizontal_scale, y, width * horizontal_scale, height)
            path = QPainterPath()
            path.addRoundedRect(rect, 18, 18)
            background, outline = ZONE_STYLES[kind]
            zone = self._scene.addPath(path, QPen(QColor(outline), 1.5), QBrush(QColor(background)))
            zone.setAcceptedMouseButtons(Qt.NoButton)
            label = self._scene.addSimpleText(text, map_font(24, bold=True))
            label.setBrush(QBrush(QColor("#526782")))
            label.setPos(rect.left() + 16, rect.top() + 12)
            label.setZValue(1)
            label.setAcceptedMouseButtons(Qt.NoButton)

        for point_name, (x, y, display_name, endpoint, major) in self.NODE_LAYOUT.items():
            kind = "base"
            if point_name == "BGIntP010":
                kind = "home"
            elif major:
                kind = "major"
            elif endpoint:
                kind = "endpoint"
            node = NodeItem(point_name, display_name, QPointF(x * horizontal_scale, y),
                            kind, self.node_clicked.emit)
            self._nodes[point_name] = node
            self._scene.addItem(node)

        for src, dst in self.EDGES:
            origin, target = self._nodes[src], self._nodes[dst]
            displacement = target.pos() - origin.pos()
            length = math.hypot(displacement.x(), displacement.y())
            direction = displacement / length
            start = edge_point(origin, direction)
            end = edge_point(target, -direction)
            arrow_size = min(9, math.hypot(end.x() - start.x(), end.y() - start.y()) / 3)

            forward = QPainterPath(start)
            forward.lineTo(end)
            add_arrowhead(forward, end, direction, arrow_size)
            reverse = QPainterPath()
            add_arrowhead(reverse, start, -direction, arrow_size)

            arrows = (
                self._scene.addPath(forward, PEN_NORMAL),
                self._scene.addPath(reverse, PEN_REVERSE),
            )
            for arrow in arrows:
                arrow.setZValue(5)
                arrow.setAcceptedMouseButtons(Qt.NoButton)
            self._edge_items[(src, dst)] = arrows

        self._scene.setSceneRect(self._scene.itemsBoundingRect().adjusted(-20, -16, 20, 16))
        self._view.fit_map()

    def _on_node_clicked(self, point_name):
        if self._selected_point:
            self._nodes[self._selected_point].set_selected(False)
        self._selected_point = point_name
        self._nodes[point_name].set_selected(True)
        self._info_label.setText(f"Выбрана точка: {point_name}")

    def set_current_position(self, point_name):
        """Отмечает текущую точку манипулятора."""
        if self._current_point is not None:
            self._nodes[self._current_point].set_current(False)
        self._current_point = point_name if point_name in self._nodes else None
        if self._current_point is None:
            self._info_label.setText(MAP_PROMPT)
            return
        self._nodes[point_name].set_current(True)
        self._info_label.setText(f"Текущая позиция: {point_name}")

    def set_point_blocked(self, point_name, blocked, reason=""):
        """Отображает состояние доступности точки."""
        node = self._nodes.get(point_name)
        if node is not None:
            node.set_blocked(blocked, reason)

    def highlight_trajectory(self, src, dst, traj_name=""):
        """Выделяет связь между точками и приглушает остальные."""
        edge = (src, dst)
        if edge not in self._edge_items:
            edge = (dst, src)
        if edge not in self._edge_items:
            self.reset_highlight()
            self._info_label.setText(f"Связь между {src} и {dst} отсутствует")
            return

        for key, arrows in self._edge_items.items():
            active = key == edge
            for arrow in arrows:
                arrow.setPen(PEN_HIGHLIGHT if active else PEN_DIM)
                arrow.setZValue(7 if active else 4)
        self._info_label.setText(f"Траектория: {traj_name or f'{src} → {dst}'}")

    def reset_highlight(self):
        """Возвращает обычное оформление связей."""
        for arrows in self._edge_items.values():
            for arrow, pen in zip(arrows, (PEN_NORMAL, PEN_REVERSE)):
                arrow.setPen(pen)
                arrow.setZValue(5)
        self._info_label.setText(MAP_PROMPT)
