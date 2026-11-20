from PyQt5.QtWidgets import QMainWindow
from PyQt5 import QtCore, QtWidgets

from led_control import LedPattern
from io_map import DO
from .ui_engineer_window import Ui_EngineerWindow


class EngineerWindow(QMainWindow):

    def __init__(self, rc, parent=None):
        super().__init__(parent)

        self.InitUI()

        self.rc = rc
        self.ui.di_M1_Ready.setChecked(True)
        self.ui.di_M1_Alarm.setChecked(True)
        # self.ui.do_G1_Clamp.setChecked(True)

    def InitUI(self):
        self.ui = Ui_EngineerWindow()
        self.ui.setupUi(self)
        self.setup_indicator_style()
        self.setup_inputs_readonly()
        self.ui.exitButton.clicked.connect(self.close)
        self.ui.mbrs_Disable.clicked.connect(self.light_off)
        self.ui.mbrs_Green.clicked.connect(self.green_light)
        self.ui.mbrs_Green_Blink.clicked.connect(self.green_blink)
        self.ui.mbrs_Yellow.clicked.connect(self.yellow_light)
        self.ui.mbrs_Yellow_Blink.clicked.connect(self.yellow_blink)
        self.ui.radioButton_6.clicked.connect(self.red_light)
        # self.ui.mbrs_Red_Blink.clicked.connect(self.red_blink)
        self.ui.do_M1_ChuckOpen.clicked.connect(self.do_m1_chuck_open)
        self.ui.do_M1_ChuckClose.clicked.connect(self.do_m1_chuck_close)
        self.ui.do_M1_StartProcess.clicked.connect(self.do_m1_start_process)
        self.ui.do_M1_StopProcess.clicked.connect(self.do_m1_stop_process)
        self.ui.do_M1_DoorClose.clicked.connect(self.do_m1_door_close)
        self.ui.do_M1_DoorIOpen.clicked.connect(self.do_m1_door_open)
        self.ui.do_M_AirSpray.clicked.connect(self.do_air_spray)
        self.ui.do_M2_ChuckOpen.clicked.connect(self.do_m2_chuck_open)
        self.ui.do_M2_ChuckClose.clicked.connect(self.do_m2_chuck_close)
        self.ui.do_M2_StartProcess.clicked.connect(self.do_m2_start_process)
        self.ui.do_M2_StopProcess.clicked.connect(self.do_m2_stop_process)
        self.ui.do_M2_DoorClose.clicked.connect(self.do_m2_door_close)
        self.ui.do_M2_DoorIOpen.clicked.connect(self.do_m2_door_open)
        self.ui.do_G1_Clamp.clicked.connect(self.do_g1_clamp)
        self.ui.do_G2_Clamp.clicked.connect(self.do_g2_clamp)
        self.ui.do_C_Switch.clicked.connect(self.do_c_switch)
        self.ui.do_Cart_Lamp.clicked.connect(self.do_cart_lamp)

    def setup_indicator_style(self):
        self.setStyleSheet("""
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

        for checkbox in self.findChildren(QtWidgets.QCheckBox):

            name = checkbox.objectName()

            if name.startswith(("di_", "mbtcp_")):
                checkbox.setAttribute(
                    QtCore.Qt.WA_TransparentForMouseEvents, True
                )

                checkbox.setFocusPolicy(QtCore.Qt.NoFocus)

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
        self.rc.io.set_do(DO.M1_SwitchChuck, True)
        # self.rc.io.set_do(DO.M1_ChuckOpen, True)
        # self.rc.io.set_do(DO.M1_ChuckClose, False)

    def do_m1_chuck_close(self):
        self.rc.io.set_do(DO.M1_SwitchChuck, False)
        # self.rc.io.set_do(DO.M1_ChuckClose, True)
        # self.rc.io.set_do(DO.M1_ChuckOpen, False)

    def do_m1_start_process(self):
        self.rc.io.set_do(DO.M1_StartProcess, True)
        # self.rc.io.set_do(DO.M1_StopProcess, False)

    def do_m1_stop_process(self):
        # self.rc.io.set_do(DO.M1_StopProcess, True)
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
        self.rc.io.set_do(DO.M2_SwitchChuck, True)
        # self.rc.io.set_do(DO.M2_ChuckOpen, True)
        # self.rc.io.set_do(DO.M2_ChuckClose, False)

    def do_m2_chuck_close(self):
        self.rc.io.set_do(DO.M2_SwitchChuck, False)
        # self.rc.io.set_do(DO.M2_ChuckClose, True)
        # self.rc.io.set_do(DO.M2_ChuckOpen, False)

    def do_m2_start_process(self):
        self.rc.io.set_do(DO.M2_StartProcess, True)
        # self.rc.io.set_do(DO.M2_StopProcess, False)

    def do_m2_stop_process(self):
        # self.rc.io.set_do(DO.M2_StopProcess, True)
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
        pass
        # self.rc.io.set_do(DO.C_Switch, True)

    def do_cart_lamp(self):
        pass
        # self.rc.io.set_do(DO.do_Cart_Lamp, True)

