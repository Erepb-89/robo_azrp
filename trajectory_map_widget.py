"""
Интерактивная карта траекторий манипулятора ЭРИ Порта.
Визуализация зон, базовых точек и маршрутов перемещения.
Отображает состояния XY-платформы и оборудования из ПЛК.
"""
from PyQt5.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsEllipseItem,
    QGraphicsRectItem, QGraphicsTextItem,
    QGraphicsPathItem, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QGraphicsItem, QFrame,
)
from PyQt5.QtCore import Qt, QPointF, pyqtSignal, QLineF
from PyQt5.QtGui import (
    QPen, QBrush, QColor, QFont, QPainterPath, QPainter,
)
import math

from config import (
    GREEN_COLOR, BEIGE_COLOR, BLUE_COLOR, ALABASTER_COLOR,
    ZONE_COLORS, ZONE_BORDER_COLORS,
    NODE_BASE_COLOR, NODE_ENDPOINT_COLOR, NODE_HOME_COLOR,
    NODE_CURRENT_COLOR, NODE_HOVER_COLOR, NODE_BLOCKED_COLOR,
    PEN_NORMAL, PEN_DIM, PEN_HL, PEN_BACK_ARROW,
    MAP_STATUS_OFF,
    GROUPS, SEP_COLOR, PORT_TYPE,
    STATIONARY_PORT_COLOR, MOBILE_PORT_COLOR, NODE_MAJOR_COLOR,
)


# ─── NodeItem ────────────────────────────────────────────────
class NodeItem(QGraphicsEllipseItem):
    """Интерактивная точка (узел) на карте траекторий."""

    def __init__(self, point_name, display_name, x, y, radius=18,
                 color=NODE_BASE_COLOR, is_endpoint=False, parent_widget=None,
                 is_major=False):
        super().__init__(-radius, -radius, radius * 2, radius * 2)
        self.point_name = point_name
        self.display_name = display_name
        self.radius = radius
        self.base_color = color
        self.is_endpoint = is_endpoint
        self.is_major = is_major
        self.parent_widget = parent_widget
        self._is_blocked = False

        self.setPos(x, y)
        self.setZValue(10)
        self.setAcceptHoverEvents(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFlag(QGraphicsItem.ItemIsSelectable, True)

        self.setBrush(QBrush(color))
        self.setPen(QPen(color.darker(140), 2))

        # Метка внутри круга
        self._label = QGraphicsTextItem(display_name, self)
        self._label.setFont(QFont("Segoe UI", 7, QFont.Bold))
        self._label.setDefaultTextColor(Qt.white)
        br = self._label.boundingRect()
        self._label.setPos(-br.width() / 2, -br.height() / 2)

        # Тултип
        self._tooltip = QGraphicsTextItem(point_name, self)
        self._tooltip.setFont(QFont("Segoe UI", 10))
        self._tooltip.setDefaultTextColor(QColor(30, 30, 30))
        self._tooltip.setZValue(100)
        self._tooltip.setVisible(False)
        tbr = self._tooltip.boundingRect()
        self._tooltip.setPos(-tbr.width() / 2, +radius + tbr.height() + 4)

    def hoverEnterEvent(self, event):
        if not self._is_blocked:
            self.setBrush(QBrush(NODE_HOVER_COLOR))
            self.setPen(QPen(NODE_HOVER_COLOR.darker(150), 3))
        self._tooltip.setVisible(True)
        super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event):
        self.setBrush(QBrush(self.base_color))
        self.setPen(QPen(self.base_color.darker(140) if not self._is_blocked
                         else QColor(183, 28, 28), 2,
                         Qt.DashLine if self._is_blocked else Qt.SolidLine))
        self._tooltip.setVisible(False)
        super().hoverLeaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton and self.parent_widget:
            self.parent_widget.node_clicked.emit(self.point_name)
        super().mousePressEvent(event)

    def set_current(self, is_current: bool):
        if is_current:
            self.base_color = NODE_CURRENT_COLOR
            self.setBrush(QBrush(NODE_CURRENT_COLOR))
            self.setPen(QPen(NODE_CURRENT_COLOR.darker(140), 3))
            self.setScale(1.3)
        else:
            if self._is_blocked:
                # Восстанавливаем заблокированный вид
                self._apply_blocked_style()
            else:
                if "pHomePosition" in self.point_name:
                    color = NODE_HOME_COLOR
                elif self.is_major:
                    color = NODE_MAJOR_COLOR
                elif self.is_endpoint:
                    color = NODE_ENDPOINT_COLOR
                else:
                    color = NODE_BASE_COLOR
                self.base_color = color
                self.setBrush(QBrush(color))
                self.setPen(QPen(color.darker(140), 2))
                self.setScale(1.0)

    def set_blocked(self, blocked: bool, reason: str = ""):
        self._is_blocked = blocked
        if blocked:
            self._apply_blocked_style()
            self._tooltip.setPlainText(f"{self.point_name}\n🔒 {reason}")
        else:
            if "pHomePosition" in self.point_name:
                color = NODE_HOME_COLOR
            elif self.is_major:
                color = NODE_MAJOR_COLOR
            elif self.is_endpoint:
                color = NODE_ENDPOINT_COLOR
            else:
                color = NODE_BASE_COLOR
            self.base_color = color
            self.setBrush(QBrush(color))
            self.setPen(QPen(color.darker(140), 2))
            self.setScale(1.0)
            self._tooltip.setPlainText(self.point_name)

    def _apply_blocked_style(self):
        self.base_color = NODE_BLOCKED_COLOR
        self.setBrush(QBrush(NODE_BLOCKED_COLOR))
        self.setPen(QPen(QColor(183, 28, 28), 2, Qt.DashLine))
        self.setScale(1.0)


# ─── Стрелка ─────────────────────────────────────────────────
def _make_arrow_path(p1: QPointF, p2: QPointF, arrow_size=8) -> QPainterPath:
    line = QLineF(p1, p2)
    angle = math.atan2(-line.dy(), line.dx())
    ap1 = p2 - QPointF(math.cos(angle - math.pi / 6) * arrow_size,
                       -math.sin(angle - math.pi / 6) * arrow_size)
    ap2 = p2 - QPointF(math.cos(angle + math.pi / 6) * arrow_size,
                       -math.sin(angle + math.pi / 6) * arrow_size)
    path = QPainterPath()
    path.moveTo(p1)
    path.lineTo(p2)
    path.moveTo(p2)
    path.lineTo(ap1)
    path.moveTo(p2)
    path.lineTo(ap2)
    return path


# ─── Главный виджет ──────────────────────────────────────────
class TrajectoryMapWidget(QWidget):
    """
    Виджет с интерактивной картой траекторий манипулятора.
    Показывает текущую позицию манипулятора, состояния XY-платформы
    и оборудования из ПЛК.
    """
    node_clicked = pyqtSignal(str)

    NODE_LAYOUT = {                                          #node_x, node_y, display, is_endpoint, is_major
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
        self._current_point = None
        self._nodes: dict[str, NodeItem] = {}
        self._edge_items: dict[tuple, list] = {}
        self._status_labels: dict[str, QLabel] = {}  # key → bottom panel label
        self._init_ui()

    # ── UI ────────────────────────────────────────────────────
    def _init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)

        title = QLabel("Схема траекторий манипулятора ЭРИ Порта")
        title.setFont(QFont("Segoe UI", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)

        # Индикатор типа порта
        _port_label_text = "ЭРИ-Порт: стационарный" \
            if PORT_TYPE == "stationary" \
            else "ЭРИ-Порт: мобильный"
        _port_label_style = (
            STATIONARY_PORT_COLOR
            if PORT_TYPE == "stationary"
            else MOBILE_PORT_COLOR
        )
        port_badge = QLabel(_port_label_text)
        port_badge.setStyleSheet(_port_label_style)
        port_badge.setAlignment(Qt.AlignCenter)
        layout.addWidget(port_badge)

        # Легенда
        legend = QHBoxLayout()
        legend.addStretch()
        for lbl_text, node_color in [
            ("Home", NODE_HOME_COLOR),
            ("Базовая точка", NODE_BASE_COLOR),
            ("Конечная точка", NODE_ENDPOINT_COLOR),
            ("Зона недоступна", NODE_BLOCKED_COLOR),
            ("Текущая позиция", NODE_CURRENT_COLOR),
        ]:
            dot = QLabel("●")
            dot.setFont(QFont("Segoe UI", 14))
            dot.setStyleSheet(f"color: {node_color.name()};")
            txt = QLabel(lbl_text)
            txt.setFont(QFont("Segoe UI", 9))
            legend.addWidget(dot)
            legend.addWidget(txt)
            legend.addSpacing(12)
        legend.addStretch()
        layout.addLayout(legend)

        self._info_label = QLabel("Нажмите на точку для выбора маршрута")
        self._info_label.setFont(QFont("Segoe UI", 10))
        self._info_label.setAlignment(Qt.AlignCenter)
        self._info_label.setStyleSheet(BLUE_COLOR)
        layout.addWidget(self._info_label)

        self._scene = QGraphicsScene()
        self._view = QGraphicsView(self._scene)
        self._view.setRenderHint(QPainter.Antialiasing)
        self._view.setRenderHint(QPainter.SmoothPixmapTransform)
        self._view.setDragMode(QGraphicsView.ScrollHandDrag)
        self._view.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
        self._view.setResizeAnchor(QGraphicsView.AnchorUnderMouse)
        self._view.setStyleSheet(ALABASTER_COLOR)
        layout.addWidget(self._view, stretch=1)

        # ── Панель состояния ПЛК ──────────────────────────────
        layout.addWidget(self._build_status_panel())

        self._build_scene()
        self._view.fitInView(
            self._scene.sceneRect().adjusted(-30, -30, 30, 30),
            Qt.KeepAspectRatio)

        self.node_clicked.connect(self._on_node_clicked)

    def _build_status_panel(self) -> QWidget:
        """Нижняя панель с компактными индикаторами ПЛК."""
        panel = QWidget()
        row = QHBoxLayout(panel)
        row.setContentsMargins(6, 2, 6, 2)
        row.setSpacing(4)

        for group_name, items in GROUPS:
            hdr = QLabel(group_name + ":")
            hdr.setFont(QFont("Segoe UI", 8, QFont.Bold))
            row.addWidget(hdr)
            for key, default_text in items:
                lbl = QLabel(default_text)
                lbl.setFont(QFont("Segoe UI", 8))
                lbl.setAlignment(Qt.AlignCenter)
                lbl.setFrameStyle(QFrame.Panel | QFrame.Sunken)
                lbl.setStyleSheet(MAP_STATUS_OFF)
                lbl.setMinimumWidth(80)
                row.addWidget(lbl)
                self._status_labels[key] = lbl

            sep = QFrame()
            sep.setFrameShape(QFrame.VLine)
            sep.setStyleSheet(SEP_COLOR)
            row.addWidget(sep)

        row.addStretch()
        return panel

    # ── Сцена ─────────────────────────────────────────────────
    def _build_scene(self):
        self._scene.clear()
        self._nodes.clear()
        self._edge_items.clear()

        # 1) Зоны + XY-чип платформы в каждой зоне
        for (zone_x, zone_y, zone_w, zone_h, zone_type, zone_label) in self.ZONES:
            rect = QGraphicsRectItem(zone_x, zone_y, zone_w, zone_h)
            rect.setBrush(QBrush(ZONE_COLORS[zone_type]))
            rect.setPen(QPen(ZONE_BORDER_COLORS[zone_type], 2, Qt.DashLine))
            rect.setZValue(0)
            self._scene.addItem(rect)

            zlbl = QGraphicsTextItem(zone_label)
            zlbl.setFont(QFont("Segoe UI", 8, QFont.Bold))
            zlbl.setDefaultTextColor(ZONE_BORDER_COLORS[zone_type].darker(120))
            zlbl.setPos(zone_x + 5, zone_y + 2)
            zlbl.setZValue(1)
            self._scene.addItem(zlbl)

        # 4) Рёбра
        TRIM = 20
        for (src, dst) in self.EDGES:
            if src not in self.NODE_LAYOUT or dst not in self.NODE_LAYOUT:
                continue  # пропускаем отсутствующие узлы
            src_x, src_y = self.NODE_LAYOUT[src][:2]
            dst_x, dst_y = self.NODE_LAYOUT[dst][:2]
            edge_start, edge_end = QPointF(src_x, src_y), QPointF(dst_x, dst_y)
            length = QLineF(edge_start, edge_end).length()
            if length < 1:
                continue
            trim_ratio = TRIM / length
            trim_start = QPointF(src_x + (dst_x - src_x) * trim_ratio,
                                 src_y + (dst_y - src_y) * trim_ratio)
            trim_end = QPointF(dst_x - (dst_x - src_x) * trim_ratio,
                               dst_y - (dst_y - src_y) * trim_ratio)

            forward_arrow = QGraphicsPathItem(_make_arrow_path(trim_start, trim_end, 7))
            forward_arrow.setPen(PEN_NORMAL)
            forward_arrow.setZValue(5)
            self._scene.addItem(forward_arrow)

            backward_arrow = QGraphicsPathItem(_make_arrow_path(trim_end, trim_start, 7))
            backward_arrow.setPen(PEN_BACK_ARROW)
            backward_arrow.setZValue(5)
            self._scene.addItem(backward_arrow)

            self._edge_items[(src, dst)] = [forward_arrow, backward_arrow]

        # 5) Узлы
        for point_name, (node_x, node_y, display, is_endpoint, is_major) in self.NODE_LAYOUT.items():
            if "pHomePosition" in point_name:
                color, radius = NODE_HOME_COLOR, 20
            elif is_major:
                color, radius = NODE_MAJOR_COLOR, 18
            elif is_endpoint:
                color, radius = NODE_ENDPOINT_COLOR, 16
            else:
                color, radius = NODE_BASE_COLOR, 18

            node = NodeItem(
                point_name, display, node_x, node_y,
                radius=radius,
                color=color,
                is_endpoint=is_endpoint,
                parent_widget=self,
                is_major=is_major,
            )
            self._scene.addItem(node)
            self._nodes[point_name] = node

    # ── Публичный API ─────────────────────────────────────────
    def set_current_position(self, point_name: str):
        """Подсвечивает текущую позицию манипулятора на карте (зелёный)."""
        if self._current_point and self._current_point in self._nodes:
            self._nodes[self._current_point].set_current(False)
        self._current_point = point_name
        if point_name in self._nodes:
            self._nodes[point_name].set_current(True)
            self._info_label.setText(f"Текущая позиция: {point_name}")
            self._info_label.setStyleSheet(BEIGE_COLOR)

    def highlight_trajectory(self, src: str, dst: str, traj_name: str = ""):
        """Подсвечивает ребро src↔dst, остальные рёбра приглушает."""
        for (edge_src, edge_dst), edge_arrows in self._edge_items.items():
            is_highlighted = (edge_src == src and edge_dst == dst) or (edge_src == dst and edge_dst == src)
            if is_highlighted:
                for item in edge_arrows:
                    item.setPen(PEN_HL)
                    item.setZValue(7)
            else:
                for item in edge_arrows:
                    item.setPen(PEN_DIM)
                    item.setZValue(4)

        label = traj_name if traj_name else f"{src} → {dst}"
        self._info_label.setText(f"Траектория: {label}")
        self._info_label.setStyleSheet(GREEN_COLOR)

    def reset_highlight(self):
        """Сбрасывает подсветку всех рёбер."""
        for (_, _), edge_arrows in self._edge_items.items():
            edge_arrows[0].setPen(PEN_NORMAL)
            edge_arrows[0].setZValue(5)
            edge_arrows[1].setPen(PEN_BACK_ARROW)
            edge_arrows[1].setZValue(5)
        self._info_label.setText("Нажмите на точку для выбора маршрута")
        self._info_label.setStyleSheet(BLUE_COLOR)

    def update_plc_state(self, platform) -> None:
        """
        Обновляет визуализацию ПЛК-состояния на карте.
          platform : ManipulatorPoints | None
        """
        self._update_node_blocking(platform)

    def _update_node_blocking(self, platform=None) -> None:
        """Снимает блокировку с узлов карты (кроме текущей позиции)."""
        for point_name, node in self._nodes.items():
            # if point_name == "pHomePosition":
            #     node.set_blocked(False)
            #     continue
            if point_name == self._current_point:
                continue  # текущую позицию не трогаем

            node.set_blocked(False)

    # ── Внутренние обработчики ────────────────────────────────
    def _on_node_clicked(self, point_name: str):
        self._info_label.setText(f"Выбрана точка: {point_name}")
        self._info_label.setStyleSheet(GREEN_COLOR)

    def wheelEvent(self, event):
        factor = 1.15 if event.angleDelta().y() > 0 else 1 / 1.15
        self._view.scale(factor, factor)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._view.fitInView(
            self._scene.sceneRect().adjusted(-30, -30, 30, 30),
            Qt.KeepAspectRatio)
