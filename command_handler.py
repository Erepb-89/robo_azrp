import time
import threading
from queue import Queue
from commands import Command, CmdType
from config import GRIPPER_DO_INDEX
from typing import Optional


class CommandHandler:

    def __init__(self, robot_controller, cmd_queue: Queue, logger,
                 heartbeat_cb=None):
        self.RobotController = robot_controller
        self.cmd_queue = cmd_queue
        self.log = logger

        self.running = False
        self.stop_event = threading.Event()

        self._heartbeat_cb = heartbeat_cb

        self.traj_prev = 0
        self.act_prev = 0
        self.gcmd_prev = 0
        self.power_on_prev = 0
        self.free_drive_prev = 0
        self.find_nearest = 0

        self.trajectory = 0
        self.action = 0
        self.free_drive = 0
        self.gripper_command = 0
        self.power_on = 0

        self._last_nearest_wp: Optional[str] = None
        self._last_nearest_traj: Optional[str] = None
        self._last_nearest_dist: Optional[float] = None
        self._last_traj_state: Optional[int] = 0
        self._last_action_state: Optional[int] = 0

    def set_trajectory(self, value):
        self.trajectory = value

    def set_action(self, value):
        self.action = value

    def start(self) -> None:
        self.running = True

        try:
            while not self.stop_event.is_set():
                try:
                    self.handle_power_cmd()
                    self.handle_traj_cmd()
                    self.handle_action_cmd()
                    self.handle_free_drive_cmd()
                    self.handle_gripper_cmd()
                    # self.update_nearest_info()

                except Exception as e:
                    self.log.error(f"Error in command handler loop: {e}")

                if self._heartbeat_cb:
                    try:
                        self._heartbeat_cb('handler')
                    except Exception:
                        pass

                time.sleep(0.2)

        finally:
            self.log.info("Command handler stopped.")

    def handle_power_cmd(self) -> None:  # 1 = ON, 0 = OFF
        if self.power_on_prev != self.power_on:
            self.cmd_queue.put(Command(CmdType.POWER,
                                       {'state': int(self.power_on)},
                                       source="CMD"))
        self.power_on_prev = self.power_on

    def handle_traj_cmd(self):
        if self.traj_prev != self.trajectory:
            if self.trajectory == 0:
                self.cmd_queue.put(
                    Command(CmdType.STOP_MOVE, {},
                            source="CMD"))
            else:
                if self.trajectory in range(1, 999):
                    self.cmd_queue.put(
                        Command(CmdType.EXECUTE_TRAJECTORY, {'num': int(self.trajectory)},
                                source="CMD"))
        self.traj_prev = self.trajectory

    def handle_action_cmd(self):
        if self.act_prev != self.action:
            if self.action == 0:
                self.cmd_queue.put(
                    Command(CmdType.STOP_MOVE, {},
                            source="CMD"))
            else:
                if self.action in range(1, 999):
                    self.cmd_queue.put(
                        Command(CmdType.EXECUTE_ACTION, {'num': int(self.action)},
                                source="CMD"))
        self.act_prev = self.action

    def handle_free_drive_cmd(self) -> None:  # 1 = ON, 0 = OFF
        if self.free_drive_prev != self.free_drive:
            self.cmd_queue.put(Command(CmdType.FREE_DRIVE,
                                       {'state': int(self.free_drive)},
                                       source="CMD"))
        self.free_drive_prev = self.free_drive

    def handle_gripper_cmd(self) -> None:  # 1 = ON, 0 = OFF
        try:
            if self.gcmd_prev != self.gripper_command:
                self.cmd_queue.put(Command(CmdType.GRIPPER_CMD,
                                           {'index': GRIPPER_DO_INDEX,
                                            'value': bool(self.gripper_command)},
                                           source="CMD"))
            self.gcmd_prev = self.gripper_command
        except Exception as e:
            raise RuntimeError(f"qGripperCommand Error, {e}")

    def stop(self) -> None:
        self.stop_event.set()
