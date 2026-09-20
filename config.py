from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen

BASE_DIR = Path(__file__).resolve().parent

# Пути к данным
POINTS_PATH = BASE_DIR / "points.json"
TRAJ_PATH = BASE_DIR / "trajectories.json"

# Параметры подключения
ROBOT_IP = "127.0.0.1"

# Команды
EXEC_TRAJ = "EXECUTE_TRAJECTORY"
GRIPPER_CMD = "GRIPPER_CMD"

# IO и прочее
NUM_DIGITAL_IO = 24
GRIPPER_1_DO_INDEX = 0
GRIPPER_2_DO_INDEX = 1
ZONE_SENSOR_DI = 1
LOG_PATH = BASE_DIR / "robopro.log"

"""Состояния выполнения команды"""
EXECUTION = 100
FINISHED = 200
EXCEPTION = 300
BLOCK = 400

# стили для trajectory_map
RED_COLOR = "background:#fce4ec; border-radius:6px; padding:6px; color:#b71c1c;"
GREEN_COLOR = "background:#e8f5e9; border-radius:6px; padding:6px; color:#2e7d32; font-weight:bold;"
BEIGE_COLOR = "background:#fff3e0; border-radius:6px; padding:6px; color:#e65100; font-weight:bold;"
BLUE_COLOR = "background:#e3f2fd; border-radius:6px; padding:6px; color:#1565c0;"
ALABASTER_COLOR = "border:none; background:#fafafa;"
STATIONARY_PORT_COLOR = "padding:2px 10px; border-radius:4px; font-size:11px; background:#e8f5e9; color:#2e7d32;"
MOBILE_PORT_COLOR = "padding:2px 10px; border-radius:4px; font-size:11px; background:#e3f2fd; color:#1565c0;"

# ── UI стили ────────────────────────────────────────────────────────────────

# Журнал операций
JOURNAL_COUNT = 1000

LOG_STYLESHEET = (
    f"QListWidget {{ font-family: 'Consolas', monospace; font-size: 16px; }}"
)
LOG_COLOR_NEUTRAL = "#555555"  # обычные GUI-команды
LOG_COLOR_STOP = "#e65100"  # стоп / предупреждение
LOG_COLOR_CMD = "#1565c0"  # команды от хендлера
LOG_COLOR_ERROR = "#b71c1c"  # ошибка / заблокировано
LOG_COLOR_SUCCESS = "#2e7d32"  # успешное завершение

LABEL_PADDING = "padding:2px 8px;"

# Индикаторы подключения в статус-баре
CONN_ONLINE_STYLE = "padding:2px 6px; color: #1b5e20; background: #c8e6c9;"
CONN_OFFLINE_STYLE = "padding:2px 6px; color: #b71c1c; background: #ffcdd2;"
CONN_INIT_STYLE = "padding:2px 6px; color: #9e9e9e;"

COMMON_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #E1E1E1;"
    "  border-radius: 5px;"
    "  border-style: solid;"
    "  border-color: #212121;"
    "  border-width: 1px;"
    "}"
    "QPushButton:hover { background-color: #d2d2d2; }"
    "QPushButton:pressed { background-color: #BEBEBE; }"
)

GREEN_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #7CFC00;"
    "  border-radius: 5px;"
    "  border-style: solid;"
    "  border-color: #212121;"
    "  border-width: 1px;"
    "}"
    "QPushButton:hover { background-color: #d2d2d2; }"
    "QPushButton:pressed { background-color: #BEBEBE; }"
)

ACTIVATED_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #BEBEBE;"
    "  border-radius: 5px;"
    "  border-style: solid;"
    "  border-color: #212121;"
    "  border-width: 1px;"
    "}"
    "QPushButton:hover { background-color: #d2d2d2; }"
    "QPushButton:pressed { background-color: #E1E1E1; }"
)

# Кнопки верхнего тулбара
GRIPPER_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #626262;"
    "  color: white;"
    "  border-radius: 5px;"
    "  padding: 4px 16px;"
    "}"
    "QPushButton:hover { background-color: #828282; }"
    "QPushButton:pressed { background-color: #b71c1c; }"
)
STOP_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #424242;"
    "  color: white;"
    "  border-radius: 5px;"
    "  padding: 4px 16px;"
    "}"
    "QPushButton:hover { background-color: #e53935; }"
    "QPushButton:pressed { background-color: #b71c1c; }"
)
POWER_OFF_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #d32f2f;"
    "  color: white;"
    "  border-radius: 5px;"
    "  padding: 4px 16px;"
    "}"
    "QPushButton:hover { background-color: #424242; }"
    "QPushButton:pressed { background-color: #212121; }"
)
MOVE_BTN_STYLE = (
    "QPushButton {"
    "  background-color: #2e7d32;"
    "  color: white;"
    "  border-radius: 5px;"
    "  padding: 4px 16px;"
    "}"
    "QPushButton:hover { background-color: #242424; }"
    "QPushButton:pressed { background-color: #b71c1c; }"
)

# Подсветка кнопок питания
POWER_ON_ACTIVE_STYLE = "background: rgb(124,252,0);"
POWER_OFF_ACTIVE_STYLE = "background: rgb(255,0,0);"
POWER_BTN_INACTIVE_STYLE = "background: rgb(240,240,240);"

# ── Карта траекторий: цвета зон ───────────────────────────────
ZONE_COLORS = {
    "Device1": QColor(41, 98, 255, 30),
    "Table": QColor(255, 152, 0, 30),
    "grippers": QColor(255, 152, 0, 30),
    "Device2": QColor(76, 175, 80, 30),
}
ZONE_BORDER_COLORS = {
    "Device1": QColor(41, 98, 255, 180),
    "Table": QColor(255, 152, 0, 180),
    "grippers": QColor(255, 152, 0, 180),
    "Device2": QColor(76, 175, 80, 180),
}

# ── Карта траекторий: цвета узлов ─────────────────────────────
NODE_BASE_COLOR = QColor(41, 98, 255)
NODE_MAJOR_COLOR = QColor(255, 163, 7)
NODE_ENDPOINT_COLOR = QColor(255, 87, 34)
NODE_HOME_COLOR = QColor(244, 67, 54)
NODE_CURRENT_COLOR = QColor(76, 175, 80)
NODE_HOVER_COLOR = QColor(255, 193, 7)
NODE_BLOCKED_COLOR = QColor(190, 190, 190)

# ── Карта траекторий: перья рёбер ─────────────────────────────
PEN_NORMAL = QPen(QColor(100, 100, 100, 180), 1.8)
PEN_DIM = QPen(QColor(180, 180, 180, 70), 1.0, Qt.PenStyle.DotLine)
PEN_HL = QPen(QColor(255, 152, 0, 240), 3.5)
PEN_BACK_ARROW = QPen(QColor(100, 100, 100, 120), 1.5)

# ── Карта траекторий: стили статус-меток ──────────────────────
MAP_STATUS_OK = "padding:1px 4px; color:#1b5e20; background:#c8e6c9;"
MAP_STATUS_WARN = "padding:1px 4px; color:#e65100; background:#fff3e0;"
MAP_STATUS_ALM = "padding:1px 4px; color:#b71c1c; background:#ffcdd2;"
MAP_STATUS_OFF = "padding:1px 4px; color:#9e9e9e; background:#f5f5f5;"
