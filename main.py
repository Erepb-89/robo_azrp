import logging
import sys
import threading
from queue import Queue
from PyQt5 import QtWidgets

from config import ROBOT_IP, LOG_PATH
from command_handler import CommandHandler
from utils import setup_logging
from robot_controller import RobotController
from ui_form_wp_gen import MainWindow
from commands import Command, CmdType

from heartbeat import Heartbeat
from watchdog_manager import WatchdogManager


class MainAppClass:
    def __init__(self):
        self.logger = setup_logging(LOG_PATH)
        self.intentional_exit = False

        self.heartbit = Heartbeat(names=['rc', 'handler'], ttl_sec=10.0)

        self.cmd_queue = Queue(maxsize=1000)

        self.RobotController = RobotController(ROBOT_IP,
                                               self.cmd_queue,
                                               self.logger,
                                               heartbeat_cb=self.heartbit.beat)
        self.ControllerThread = threading.Thread(
            target=self.RobotController.run,
            name="RobotControllerThread", daemon=True)
        self.ControllerThread.start()

        self.rc_ready = threading.Event()
        self.CommandHandler = CommandHandler(self.RobotController,
                                             self.cmd_queue,
                                             self.logger,
                                             heartbeat_cb=self.heartbit.beat)
        self.CommandHandlerThread = threading.Thread(target=self.CommandHandler.start,
                                                     name="CommandHandlerThread", daemon=True)
        self.CommandHandlerThread.start()

        self.watchdog = WatchdogManager(self.heartbit, interval_sec=5.0,
                                        logger=self.logger)
        self.watchdog.start()

        self.App = QtWidgets.QApplication([])

        self.Form = MainWindow(
            self.RobotController,
            self.cmd_queue,
            self.CommandHandler,
            heartbeat=self.heartbit
        )
        self.Form.closeEvent = self.on_close
        self.Form.show()

        self.watchdog.set_ready()
        self.logger.info("READY=1 sent")

    def hide_form(self, event):
        self.Form.hide()
        event.ignore()

    def on_close(self, event):
        self.watchdog.stop()
        self.intentional_exit = True
        try:
            self.cmd_queue.put_nowait(
                Command(CmdType.SHUTDOWN, {}, source="APP"))
        except Exception as e:
            print(e)
        self.CommandHandler.stop()
        self.RobotController.stop()

        event.accept()

    def run(self):
        self.App.exec_()


def main():
    try:
        app = MainAppClass()
        code = app.run()
        return 0
    except Exception:
        logging.exception("FATAL: unhandled exception")
        return 1


if __name__ == "__main__":
    sys.exit(main())
