import logging
from functools import partial
from pathlib import Path

from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtGui, QtWidgets

from .trajectory_map import TrajectoryMapWidget
from .ui_engineer_window import Ui_EngineerWindow

from led_control import LedPattern
from io_map import DO

UI_DIR = Path(__file__).resolve().parent
STYLE_PATH = UI_DIR / "style.qss"

INPUT_SIGNALS = (
    ('di_Check_Button', 'X224:0', 'Сигнал с кнопки юстировки'),
    ('di_M1_DoorOpen', 'X224:1', 'Станок 1. Дверь открыта'),
    ('di_M1_DoorClose', 'X224:2', 'Станок 1. Дверь закрыта'),
    ('di_M1_Ready', 'X224:3', 'Станок 1 готов к загрузке или выгрузке'),
    ('di_M1_ChuckClamped', 'X224:4', 'Станок 1. Захват закрыт'),
    ('di_M1_ChuckRelax', 'X224:5', 'Станок 1. Захват открыт'),
    ('di_M1_Alarm', 'X224:6', 'Станок 1. Сигнал об ошибке'),
    ('di_M2_Alarm', 'X224:7', 'Станок 2. Сигнал об ошибке'),
    ('di_M2_DoorOpen', 'X225:8', 'Станок 2. Дверь открыта'),
    ('di_M2_DoorClose', 'X225:9', 'Станок 2. Дверь закрыта'),
    ('di_M2_Ready', 'X225:10', 'Станок 2 готов к загрузке или выгрузке'),
    ('di_M2_ChuckClamped', 'X225:11', 'Станок 2. Захват закрыт'),
    ('di_M2_ChuckRelax', 'X225:12', 'Станок 2. Захват открыт'),
    ('di_G1_Clamped', 'X225:13', 'Гриппер 1. Гриппер закрыт'),
    ('di_G1_Relax', 'X225:14', 'Гриппер 1. Гриппер открыт'),
    ('di_G2_Clamped', 'X225:15', 'Гриппер 2. Гриппер закрыт'),
    ('di_G2_Relax', 'X226:16', 'Гриппер 2. Гриппер открыт'),
    ('di_Gate_Sensor', 'X226:17', 'Сигнал с калитки'),
    ('di_S1_Open', 'X226:18', 'Полка 1 выдвинута'),
    ('di_S2_Open', 'X226:19', 'Полка 2 выдвинута'),
    ('di_S3_Open', 'X226:20', 'Полка 3 выдвинута'),
    ('di_S1_Close', 'X226:21', 'Полка 1 задвинута'),
    ('di_S2_Close', 'X226:22', 'Полка 2 задвинута'),
    ('di_S3_Close', 'X226:23', 'Полка 3 задвинута'),
    ('mbtcp_START_STOP', 'Modbus TCP · Din 0', 'Старт/Стоп работы робота'),
    ('mbtcp_M1_DoorAuto', 'Modbus TCP · Din 1', 'Станок 1. Дверь в автоматическом режиме работы'),
    ('mbtcp_M2_DoorAuto', 'Modbus TCP · Din 2', 'Станок 2. Дверь в автоматическом режиме работы'),
    ('mbtcp_G1_Switch', 'Modbus TCP · Din 3', 'Переключение гриппера 1'),
    ('mbtcp_G2_Switch', 'Modbus TCP · Din 4', 'Переключение гриппера 2'),
    ('mbtcp_Pause_Resume', 'Modbus TCP · Din 5', 'Пауза/Продолжить'),
    ('mbtcp_C1_SensorOpened', 'Modbus TCP · Din 6', 'Сигнал с пневмоцилиндра Поршень 1 открыт'),
    ('mbtcp_C1_SensorClosed', 'Modbus TCP · Din 7', 'Сигнал с пневмоцилиндра Поршень 1 закрыт'),
    ('mbtcp_C2_SensorOpened', 'Modbus TCP · Din 8', 'Сигнал с пневмоцилиндра Поршень 2 открыт'),
    ('mbtcp_C2_SensorClosed', 'Modbus TCP · Din 9', 'Сигнал с пневмоцилиндра Поршень 2 закрыт'),
    ('mbtcp_C_Sensor', 'Modbus TCP · Din 10', 'Тележка установлена'),
)

DISCRETE_OUTPUT_SIGNALS = (
    ('do_M1_ChuckOpen', 'X227:0', 'Станок 1. Сигнал на открытие захвата станка'),
    ('do_M1_ChuckClose', 'X227:1', 'Станок 1. Сигнал на закрытие захвата станка'),
    ('do_M1_StartProcess', 'X227:2', 'Станок 1. Старт обработки'),
    ('do_M1_StopProcess', 'X227:3', 'Станок 1. Завершение обработки'),
    ('do_M1_DoorClose', 'X227:4', 'Станок 1. Закрыть дверь в автоматическом режиме от робота'),
    ('do_M1_DoorOpen', 'X227:5', 'Станок 1. Открыть дверь в автоматическом режиме от робота'),
    ('do_M_AirSpray', 'X227:6', 'Подача воздуха. Пневмораспредилитель'),
    ('do_M2_ChuckOpen', 'X227:7', 'Станок 2. Сигнал на открытие захвата станка'),
    ('do_M2_ChuckClose', 'X228:8', 'Станок 2. Сигнал на закрытие захвата станка'),
    ('do_M2_StartProcess', 'X228:9', 'Станок 2. Старт обработки'),
    ('do_M2_StopProcess', 'X228:10', 'Станок 2. Завершение обработки'),
    ('do_M2_DoorClose', 'X228:11', 'Станок 2. Закрыть дверь в автоматическом режиме от робота'),
    ('do_M2_DoorOpen', 'X228:12', 'Станок 2. Открыть дверь в автоматическом режиме от робота'),
    ('do_G1_Clamp', 'X228:13', 'Гриппер 1.Сжать/разжать'),
    ('do_G2_Clamp', 'X228:14', 'Гриппер 2.Сжать/разжать'),
    ('do_C_Switch', 'X228:15', 'Зажим тележки. Пневмоцилиндр-4шт'),
    ('do_Cart_Lamp', 'X229:16', 'Светодиод «Наличие тележки»'),
)


class EngineerWindow(QMainWindow):
    shutdown_requested = QtCore.pyqtSignal()

    def __init__(self, rc, parent=None):
        super().__init__(parent, QtCore.Qt.Window | QtCore.Qt.FramelessWindowHint)

        self.InitUI()

        self.rc = rc
        # self.ui.di_M1_Ready.setChecked(True)
        # self.ui.di_M1_Alarm.setChecked(True)
        # self.ui.do_G1_Clamp.setChecked(True)

    def InitUI(self):
        self.ui = Ui_EngineerWindow()
        self.ui.setupUi(self)
        self.setup_indicator_style()
        self.setup_inputs_readonly()
        self.setup_input_signals_table()
        self.setup_input_simulation_table()
        self.setup_output_signals_table()
        self.setup_led_modes_table()
        self.trajectory_map = TrajectoryMapWidget(self.ui.tab_3)
        self.ui.trajectoryMapLayout.addWidget(self.trajectory_map)
        self.ui.exitButton.clicked.connect(self.close)
        self.ui.powerOffButton.setIcon(QtGui.QIcon(str(UI_DIR / "power_off.png")))
        self.ui.powerOffButton.clicked.connect(self.shutdown_requested)

        self.clock_timer = QtCore.QTimer(self)
        self.clock_timer.setInterval(1000)
        self.clock_timer.timeout.connect(self.update_clock)
        self.update_clock()

        self.ui.mbrs_Disable.clicked.connect(self.light_off)
        self.ui.mbrs_Green.clicked.connect(self.green_light)
        self.ui.mbrs_Green_Blink.clicked.connect(self.green_blink)
        self.ui.mbrs_Yellow.clicked.connect(self.yellow_light)
        self.ui.mbrs_Yellow_Blink.clicked.connect(self.yellow_blink)
        self.ui.mbrs_Red.clicked.connect(self.red_light)
        self.ui.mbrs_Red_Blink.clicked.connect(self.red_blink)
        self.ui.do_M1_ChuckOpen.clicked.connect(self.do_m1_chuck_open)
        self.ui.do_M1_ChuckClose.clicked.connect(self.do_m1_chuck_close)
        self.ui.do_M1_StartProcess.clicked.connect(self.do_m1_start_process)
        self.ui.do_M1_StopProcess.clicked.connect(self.do_m1_stop_process)
        self.ui.do_M1_DoorClose.clicked.connect(self.do_m1_door_close)
        self.ui.do_M1_DoorOpen.clicked.connect(self.do_m1_door_open)
        self.ui.do_M_AirSpray.clicked.connect(self.do_air_spray)
        self.ui.do_M2_ChuckOpen.clicked.connect(self.do_m2_chuck_open)
        self.ui.do_M2_ChuckClose.clicked.connect(self.do_m2_chuck_close)
        self.ui.do_M2_StartProcess.clicked.connect(self.do_m2_start_process)
        self.ui.do_M2_StopProcess.clicked.connect(self.do_m2_stop_process)
        self.ui.do_M2_DoorClose.clicked.connect(self.do_m2_door_close)
        self.ui.do_M2_DoorOpen.clicked.connect(self.do_m2_door_open)
        self.ui.do_G1_Clamp.clicked.connect(self.do_g1_clamp)
        self.ui.do_G2_Clamp.clicked.connect(self.do_g2_clamp)
        self.ui.do_C_Switch.clicked.connect(self.do_c_switch)
        self.ui.do_Cart_Lamp.clicked.connect(self.do_cart_lamp)

    def showEvent(self, event):
        super().showEvent(event)
        self.ui.tabWidget.setFocus(QtCore.Qt.OtherFocusReason)
        self.update_clock()
        self.clock_timer.start()

    def hideEvent(self, event):
        self.clock_timer.stop()
        super().hideEvent(event)

    def update_clock(self):
        now = QtCore.QDateTime.currentDateTime()
        self.ui.timeLabel.setText(now.toString("HH:mm:ss"))
        self.ui.dateLabel.setText(now.toString("dd.MM.yyyy"))

    def setup_indicator_style(self):
        try:
            shared_style = STYLE_PATH.read_text(encoding="utf-8")
        except (OSError, UnicodeError) as error:
            logging.getLogger(__name__).warning(
                "Не удалось загрузить стиль инженерного окна %s: %s", STYLE_PATH, error
            )
            shared_style = ""

        self.setStyleSheet(shared_style + """
            QCheckBox::indicator,
            QRadioButton::indicator {
                width: 14px;
                height: 14px;
                border-radius: 7px;
                border: 1px solid #777777;
                background-color: #bdbdbd;
            }

            QCheckBox::indicator:checked,
            QRadioButton::indicator:checked {
                background-color: #4CAF50;
                border: 1px solid #388E3C;
            }
        """)

    def setup_inputs_readonly(self):
        for checkbox in self.ui.inputSignalStates.findChildren(QtWidgets.QCheckBox):
            checkbox.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, True)
            checkbox.setFocusPolicy(QtCore.Qt.NoFocus)

    @staticmethod
    def setup_signal_table(table, row_count, column_widths):
        table.setRowCount(row_count)
        table.verticalHeader().setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        table.verticalHeader().setDefaultSectionSize(46)

        header = table.horizontalHeader()
        header.setDefaultAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
        header.setMinimumHeight(48)
        header.setSectionResizeMode(QtWidgets.QHeaderView.Fixed)
        for column, width in enumerate(column_widths):
            table.setColumnWidth(column, width)
        header.setSectionResizeMode(table.columnCount() - 1, QtWidgets.QHeaderView.Stretch)
        QtWidgets.QScroller.grabGesture(table.viewport(), QtWidgets.QScroller.TouchGesture)

    @staticmethod
    def signal_text_item(text):
        item = QtWidgets.QTableWidgetItem(text)
        item.setToolTip(text)
        return item

    def setup_input_signals_table(self):
        table = self.ui.inputSignalsTable
        self.setup_signal_table(table, len(INPUT_SIGNALS), (56, 236, 314))
        table.setIconSize(QtCore.QSize(16, 16))
        icons = (self.input_status_icon("#c5ced8"), self.input_status_icon("#0c8a42"))

        for row, (object_name, port, purpose) in enumerate(INPUT_SIGNALS):
            # Сохраняем существующие QCheckBox как источник состояния и имени.
            signal = getattr(self.ui, object_name)
            indicator = QtWidgets.QTableWidgetItem()
            table.setItem(row, 0, indicator)
            update = partial(self.update_input_status, indicator, icons)
            signal.toggled.connect(update)
            update(signal.isChecked())

            for column, text in enumerate((port, signal.text(), purpose), start=1):
                table.setItem(row, column, self.signal_text_item(text))

    def setup_input_simulation_table(self):
        table = self.ui.inputSimulationTable
        self.setup_signal_table(table, len(INPUT_SIGNALS), ())
        for row, (object_name, _, _) in enumerate(INPUT_SIGNALS):
            checkbox = getattr(self.ui, f"{object_name}_Sim")
            table.setCellWidget(row, 0, checkbox)

    def setup_output_signals_table(self):
        table = self.ui.outputSignalsTable
        self.setup_signal_table(table, len(DISCRETE_OUTPUT_SIGNALS), (164, 306))
        for row, (object_name, port, purpose) in enumerate(DISCRETE_OUTPUT_SIGNALS):
            signal = getattr(self.ui, object_name)
            table.setItem(row, 0, self.signal_text_item(port))
            table.setCellWidget(row, 1, signal)
            table.setItem(row, 2, self.signal_text_item(purpose))

    def setup_led_modes_table(self):
        table = self.ui.ledModesTable
        modes = self.ui.ledModeButtonGroup.buttons()
        self.setup_signal_table(table, len(modes), ())
        for row, mode in enumerate(modes):
            table.setCellWidget(row, 0, mode)

    @staticmethod
    def input_status_icon(color):
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.setDevicePixelRatio(2)
        pixmap.fill(QtCore.Qt.transparent)
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setPen(QtCore.Qt.NoPen)
        painter.setBrush(QtGui.QColor(color))
        painter.drawEllipse(QtCore.QRectF(1, 1, 14, 14))
        painter.end()
        return QtGui.QIcon(pixmap)

    @staticmethod
    def update_input_status(item, icons, active):
        item.setIcon(icons[active])
        text = "Активен" if active else "Неактивен"
        item.setToolTip(text)
        item.setData(QtCore.Qt.AccessibleTextRole, text)

    def light_off(self):
        self.rc.led_state.set_pattern(LedPattern.OFF)

    def green_light(self):
        self.rc.led_state.set_pattern(LedPattern.GREEN_SOLID)

    def green_blink(self):
        self.rc.led_state.set_pattern(LedPattern.GREEN_BLINK)

    def yellow_light(self):
        self.rc.led_state.set_pattern(LedPattern.YELLOW_SOLID)

    def yellow_blink(self):
        self.rc.led_state.set_pattern(LedPattern.YELLOW_BLINK)

    def red_light(self):
        self.rc.led_state.set_pattern(LedPattern.RED_SOLID)

    def red_blink(self):
        self.rc.led_state.set_pattern(LedPattern.RED_BLINK)

    def do_m1_chuck_open(self):
        self.rc.io.set_do(DO.M1_ChuckOpen, True)
        self.rc.io.set_do(DO.M1_ChuckClose, False)

    def do_m1_chuck_close(self):
        self.rc.io.set_do(DO.M1_ChuckClose, True)
        self.rc.io.set_do(DO.M1_ChuckOpen, False)

    def do_m1_start_process(self):
        self.rc.io.set_do(DO.M1_StartProcess, True)
        self.rc.io.set_do(DO.M1_StopProcess, False)

    def do_m1_stop_process(self):
        self.rc.io.set_do(DO.M1_StopProcess, True)
        self.rc.io.set_do(DO.M1_StartProcess, False)

    def do_m1_door_close(self):
        self.rc.io.set_do(DO.M1_DoorCloseCMD, True)
        self.rc.io.set_do(DO.M1_DoorOpenCMD, False)

    def do_m1_door_open(self):
        self.rc.io.set_do(DO.M1_DoorOpenCMD, True)
        self.rc.io.set_do(DO.M1_DoorCloseCMD, False)

    def do_air_spray(self):
        self.rc.io.set_do(DO.M_AirSpray, True)

    def do_m2_chuck_open(self):
        self.rc.io.set_do(DO.M2_ChuckOpen, True)
        self.rc.io.set_do(DO.M2_ChuckClose, False)

    def do_m2_chuck_close(self):
        self.rc.io.set_do(DO.M2_ChuckClose, True)
        self.rc.io.set_do(DO.M2_ChuckOpen, False)

    def do_m2_start_process(self):
        self.rc.io.set_do(DO.M2_StartProcess, True)
        self.rc.io.set_do(DO.M2_StopProcess, False)

    def do_m2_stop_process(self):
        self.rc.io.set_do(DO.M2_StopProcess, True)
        self.rc.io.set_do(DO.M2_StartProcess, False)

    def do_m2_door_close(self):
        self.rc.io.set_do(DO.M2_DoorCloseCMD, True)
        self.rc.io.set_do(DO.M2_DoorOpenCMD, False)

    def do_m2_door_open(self):
        self.rc.io.set_do(DO.M2_DoorOpenCMD, True)
        self.rc.io.set_do(DO.M2_DoorCloseCMD, False)

    def do_g1_clamp(self):
        self.rc.io.set_do(DO.G1_Clamp, True)

    def do_g2_clamp(self):
        self.rc.io.set_do(DO.G2_Clamp, True)

    def do_c_switch(self):
        self.rc.io.set_do(DO.C_Switch, True)

    def do_cart_lamp(self):
        self.rc.io.set_do(DO.Cart_Lamp, True)
