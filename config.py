from pathlib import Path
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QPen

BASE_DIR = Path(__file__).resolve().parent

# Пути к данным
POINTS_PATH = BASE_DIR / "points.json"
TRAJ_PATH = BASE_DIR / "trajectories.json"
ACTIONS_PATH = BASE_DIR / "actions2.json"

# Тип порта: "stationary" — Легионер опущен, подход под хвост снизу;
#            "mobile"     — Легионер наверху, подход сверху с доворотом.
# Значение определяет, какой набор ВТОЛ-траекторий и waypoints будет активен.
# Меняется при смене конфигурации порта (до запуска приложения).
PORT_TYPE: str = "stationary"  # "stationary" | "mobile"

# Параметры подключения
ROBOT_IP = "127.0.0.1"
# OPC_ENDPOINT = "opc.tcp://0.0.0.0:4840"  # для отладки по месту
OPC_ENDPOINT = "opc.tcp://127.0.0.1:4840"  # для теста
PLC_MANIPULATOR_ADDRESS = "opc.tcp://192.168.202.212:4840/freeopcua/server/"  # для теста
PLC_VT_ADDRESS = "opc.tcp://192.168.88.101:4840/freeopcua/server/"  # для теста
PLC_VTOL_ADDRESS = "opc.tcp://192.168.88.102:4840/freeopcua/server/"  # для теста

# Команды
EXEC_TRAJ = "EXECUTE_TRAJECTORY"
GRIPPER_CMD = "GRIPPER_CMD"
WAIT_LIFT = "WAIT_VTOL_LIFT"

# IO и прочее
NUM_DIGITAL_IO = 24
GRIPPER_DO_INDEX = 0
SHIFT_GRIPPER_DO_INDEX = 1
LOG_PATH = BASE_DIR / "robopro.log"

"""Состояния выполнения команды"""
EXECUTION = 1000
FINISHED = 2000
EXCEPTION = 3000
BLOCK = 4000

# OPC
OPC_CLIENT_TIME = 1

# Максимальное время ожидания позиции лифта ВТОЛ-стола (сек).
# Если за это время лифт не достигнет нужной позиции — действие блокируется.
VTOL_LIFT_WAIT_TIMEOUT = 60

# PLC command nodes (читаются OPC клиентом, пересылаются в cmd_queue)
PLC_CMD_POWER_ON = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.qxPowerOn"
PLC_CMD_FREE_DRIVE = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.qxFreeDrive"
PLC_CMD_FIND_NEAREST = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.qxFindNearest"
PLC_CMD_GRIPPER = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.qGripperCommand"
PLC_CMD_SHIFT_GRIPPER = "|var|HCFA-PLC.Application.OPC.LocalControl.Control.qGripperHolderCommand"
PLC_CMD_ACTION = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.qAction"
PLC_CMD_TRAJECTORY = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.qTrajectory"

ENABLE_MOVE_TO_MODULE_H = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionModuleH"
ENABLE_MOVE_TO_MODULE_V = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionModuleV"
ENABLE_MOVE_TO_CHARGER_H = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionChargerH"
ENABLE_MOVE_TO_CHARGER_V = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionChargerV"
ENABLE_MOVE_TO_PAYLOAD_STORAGE = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionPayloadStorage"
ENABLE_MOVE_TO_GRIPPERS_STORAGE = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionGrippersStorage"
ENABLE_MOVE_TO_HOME = "|var|HCFA-PLC.Application.OPC.Robot.TableMovePermissions.ixPositionHome"

STATE_TRAJECTORY = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.iTrajectoryState"
STATE_ACTION = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.iActionState"
STATE_POWER = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.ixPowered"
GRIPPER_STATE = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.iGripperState"
GRIPPER_LOCKED = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.ixGripperLocked"
GRIPPER_UNLOCKED = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.ixGripperUnlocked "
STATE_NEAREST = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.ixNearestState"
GRIPPER_HOLDER_STATE = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.iGripperHolderState"
GRIPPER_HOLDER_LOCKED = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.ixGripperHolderLocked"
GRIPPER_HOLDER_UNLOCKED = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.ixGripperHolderUnlocked"
ACTUAL_POSITION = "|var|HCFA-PLC.Application.OPC.Robot.LocalControl.iActualPosition"

STATE_POSITION = "|var|HCFA-PLC.Application.OPC.Robot.State.iPosition"
STATE_CONTROLLER = "|var|HCFA-PLC.Application.OPC.Robot.State.iControllerState"
STATE_SAFETY = "|var|HCFA-PLC.Application.OPC.Robot.State.iSafetyStatus"
STATE_MODE = "|var|HCFA-PLC.Application.OPC.Robot.State.iMode"
STATE_LAST_ERROR = "|var|HCFA-PLC.Application.OPC.Robot.State.iLastError"

HELICOPTER_MODULE = ["pHelicopter1", "pHelicopter2", "pHomePosition"]
VTOL_MODULE = ["pVTOL1", "pVTOL2", "pHomePosition"]
PAYLOAD_STORAGE = ["pPayload1", "pPayload2", "pHomePosition"]
GRIPPERS_STORAGE = ["pHomePosition"]
CHARGER_H = ["pHomePosition"]
CHARGER_V = ["pHomePosition"]
HOME_POSITION = ["pHelicopterModule", "pVTOLModule", "pPayload", "pGrippers", "pCharger"]

X_POSITION_MODULE_H = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPositionModuleH"
X_POSITION_MODULE_V = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPositionModuleV"
X_POSITION_CHARGER_H = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPositionChargerH"
X_POSITION_CHARGER_V = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPositionChargerV"
X_POSITION_PAYLOAD = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPositionPayload"
X_POSITION_GRIPPER_STORAGE = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPositionGripperStorage"
X_POSITION_HAS_ZEROED = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixHasZeroed"
X_POSITION_POWERED = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixPowered"
X_POSITION_ALARM = "|var|HCFA-PLC.Application.OPC.M_Table.X.ixAlarm"

Y_POSITION_MODULE_H = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPositionModuleH"
Y_POSITION_MODULE_V = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPositionModuleV"
Y_POSITION_CHARGER_H = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPositionChargerH"
Y_POSITION_CHARGER_V = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPositionChargerV"
Y_POSITION_PAYLOAD = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPositionPayload"
Y_POSITION_GRIPPER_STORAGE = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPositionGripperStorage"
Y_POSITION_HAS_ZEROED = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixHasZeroed"
Y_POSITION_POWERED = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixPowered"
Y_POSITION_ALARM = "|var|HCFA-PLC.Application.OPC.M_Table.Y.ixAlarm"

# Watchdog узлы (ping/pong между клиентом и PLC)
OPC_WATCHDOG_WRITE_NODE = "|var|HCFA-PLC.Application.OPC.Watchdog.CheckOut"
OPC_WATCHDOG_READ_NODE = "|var|HCFA-PLC.Application.OPC.Watchdog.CheckIn"

H_TABLE_HATCH_OPENED = "|var|HCFA-PLC.Application.OPC.H_Table.Hatch.ixOpened"
H_TABLE_HATCH_CLOSED = "|var|HCFA-PLC.Application.OPC.H_Table.Hatch.ixClosed"
H_TABLE_HATCH_ALARM = "|var|HCFA-PLC.Application.OPC.H_Table.Hatch.ixAlarm"
H_TABLE_LIFT_POS_TOP = "|var|HCFA-PLC.Application.OPC.H_Table.Lift.ixPositionTop"
H_TABLE_LIFT_POS_BOTTOM = "|var|HCFA-PLC.Application.OPC.H_Table.Lift.ixPositionBottom"
H_TABLE_LIFT_ALARM = "|var|HCFA-PLC.Application.OPC.H_Table.Lift.ixAlarm"

H_BOX_LIFT_POS_TOP = "|var|HCFA-PLC.Application.OPC.H_Box.PlugChargerLift.ixTop"
H_BOX_LIFT_POS_BOTTOM = "|var|HCFA-PLC.Application.OPC.H_Box.PlugChargerLift.ixBottom"
H_BOX_LIFT_ALARM = "|var|HCFA-PLC.Application.OPC.H_Box.PlugChargerLift.ixAlarm"

V_TABLE_HATCH_OPENED = "|var|HCFA-PLC.Application.OPC.V_Table.Hatch.ixOpened"
V_TABLE_HATCH_CLOSED = "|var|HCFA-PLC.Application.OPC.V_Table.Hatch.ixClosed"
V_TABLE_HATCH_ALARM = "|var|HCFA-PLC.Application.OPC.V_Table.Hatch.ixAlarm"
V_TABLE_LIFT_POS_TOP = "|var|HCFA-PLC.Application.OPC.V_Table.Lift.ixPositionTop"
V_TABLE_LIFT_POS_BOTTOM = "|var|HCFA-PLC.Application.OPC.V_Table.Lift.ixPositionBottom"
V_TABLE_LIFT_ALARM = "|var|HCFA-PLC.Application.OPC.V_Table.Lift.ixAlarm"

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
JOURNAL_COUNT = 100

LOG_STYLESHEET = (
    f"QListWidget {{ font-family: 'Consolas', monospace; font-size: 16px; }}"
)
LOG_COLOR_NEUTRAL = "#555555"  # обычные GUI-команды
LOG_COLOR_STOP = "#e65100"  # стоп / предупреждение
LOG_COLOR_OPC = "#1565c0"  # команды от OPC
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
    "charger": QColor(156, 39, 176, 30),
}
ZONE_BORDER_COLORS = {
    "Device1": QColor(41, 98, 255, 180),
    "Table": QColor(255, 152, 0, 180),
    "grippers": QColor(255, 152, 0, 180),
    "Device2": QColor(76, 175, 80, 180),
    "charger": QColor(156, 39, 176, 180),
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
PEN_DIM = QPen(QColor(180, 180, 180, 70), 1.0, Qt.DotLine)
PEN_HL = QPen(QColor(255, 152, 0, 240), 3.5)
PEN_BACK_ARROW = QPen(QColor(100, 100, 100, 120), 1.5)

# ── Карта траекторий: стили статус-меток ──────────────────────
MAP_STATUS_OK = "padding:1px 4px; color:#1b5e20; background:#c8e6c9;"
MAP_STATUS_WARN = "padding:1px 4px; color:#e65100; background:#fff3e0;"
MAP_STATUS_ALM = "padding:1px 4px; color:#b71c1c; background:#ffcdd2;"
MAP_STATUS_OFF = "padding:1px 4px; color:#9e9e9e; background:#f5f5f5;"

# Узел → (x_attr, y_attr, название зоны)
# Текст причины строится динамически: "X-ось не у <зоны>" / "Y-ось не у <зоны>" / "XY не у <зоны>"
ZONE_BLOCK_MAP = {
    "pHelicopterModule": ("x_module_h", "y_module_h", "вертолётного модуля"),
    "pHelicopter1": ("x_module_h", "y_module_h", "вертолётного модуля"),
    "pHelicopter1Payload": ("x_module_h", "y_module_h", "вертолётного модуля"),
    "pHelicopter2": ("x_module_h", "y_module_h", "вертолётного модуля"),
    "pHelicopter2Payload": ("x_module_h", "y_module_h", "вертолётного модуля"),
    "pVTOLModule": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL1": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL1Battery": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL1Payload": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL2": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL2Battery": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL2Battery2": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pVTOL2Battery2Charge": ("x_module_v", "y_module_v", "VTOL модуля"),
    "pPayload": ("x_pos_payload", "y_pos_payload", "зоны нагрузки"),
    "pPayload1": ("x_pos_payload", "y_pos_payload", "зоны нагрузки"),
    "pPayload2": ("x_pos_payload", "y_pos_payload", "зоны нагрузки"),
    "pGrippers": ("x_pos_grippers", "y_pos_grippers", "хранилища захватов"),
    "pGrippers1": ("x_pos_grippers", "y_pos_grippers", "хранилища захватов"),
    "pGrippers2": ("x_pos_grippers", "y_pos_grippers", "хранилища захватов"),
    "pCharger": ("x_charge_h", "y_charge_h", "зарядной станции"),
    "pCharger1": ("x_charge_h", "y_charge_h", "зарядной станции"),
    "pCharger2": ("x_charge_h", "y_charge_h", "зарядной станции"),
}

# ── Статус-панель ──────────────────────
GROUPS = [
    ("Платформа XY", [
        ("x_axis", "X: —"),
        ("y_axis", "Y: —"),
        ("platform", "Поз: —"),
    ]),
    ("ВТ-стол", [
        ("h_hatch", "Люк: —"),
        ("h_lift", "Лифт: —"),
        ("h_box", "Бокс: —"),
    ]),
    ("VTOL-стол", [
        ("v_hatch", "Люк: —"),
        ("v_lift", "Лифт: —"),
    ]),
]

SEP_COLOR = "color:#ddd;"

# ── Траектории ВТОЛ в зависимости от типа порта ───────────────────────────────
#
# Стационарный: Легионер опущен хвостом к модулю манипулятора.
#   Манипулятор заходит под хвост снизу. Стол ВТОЛ в нижней позиции.
#   pVTOL2 → tVTOL2_To_VTOL2Battery — основная траектория к батарее
#
# Мобильный: Легионер наверху. Манипулятор заходит сверху под хвост,
#   затем доворот и посадка. Конкретные высоты уточняются при наладке.
#   pVTOL2 → tVTOL2_To_VTOL2Battery_Mobile — траектория для мобильного порта
#            (waypoint добавляется в points.json / trajectories.json при наладке)
#
# VTOL_TRAJECTORIES_BY_PORT: dict[str, dict[str, set]] = {
#     "stationary": {
#         "pVTOL2": {
#             "tVTOL2_To_VTOLModule",
#             "tVTOL2_To_VTOL2Battery",  # подход под хвост снизу
#         },
#         "pVTOL2Battery": {
#             "tVTOL2Battery_To_VTOL2",
#         },
#     },
#     "mobile": {
#         "pVTOL2": {
#             "tVTOL2_To_VTOLModule",
#             "tVTOL2_To_VTOL2Battery_Mobile",  # подход сверху + доворот (наладка)
#         },
#         "pVTOL2Battery": {
#             "tVTOL2Battery_Mobile_To_VTOL2",
#         },
#     },
# }

# Требуемая позиция лифта ВТОЛ перед подходом к батарее, по типу порта:
# stationary — стол внизу (Легионер опущен хвостом к манипулятору)
# mobile — стол в средней позиции (уточняется при наладке)
VTOL_LIFT_REQUIRED_POSITION: dict[str, str] = {
    "stationary": "bottom",
    "mobile": "mid",
}
