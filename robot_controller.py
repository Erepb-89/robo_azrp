import json
import sys
import math
import threading
import dataclasses
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional
from queue import Queue, Empty

from actions import actions
from config import POINTS_PATH, TRAJ_PATH, GRIPPER_DO_INDEX, SHIFT_GRIPPER_DO_INDEX, EXECUTION, \
    FINISHED, BLOCK, EXCEPTION, \
    EXEC_TRAJ, GRIPPER_CMD, PORT_TYPE
from commands import Command, CmdType, RobotTrajectories, RobotActions, RobotPoints
from states_modes_errors import ControllerState, SafetyStatus, MotionMode, LastError

sys.path.append("robot-api")
from API.source.core.exceptions.data_validation_error.generic_error import (
    FunctionTimeOutError)
from API.source.models.classes.enum_classes.state_classes import (
    InComingControllerState as Ics,
    InComingSafetyStatus as Iss)


@dataclass
class RobotState:
    controller_state: ControllerState = ControllerState(0)
    safety_status: SafetyStatus = SafetyStatus(3)
    tcp_position: List[float] = field(default_factory=lambda: [0.0] * 6)
    joint_position: List[float] = field(default_factory=lambda: [0.0] * 6)
    mode: Optional[MotionMode] = 0
    powered: bool = False
    free_drive: bool = False
    last_error: Optional[LastError] = 0  # Optional[str] = None
    last_command: Optional[str] = None
    trajectory_state: int = 0
    action_state: int = 0
    gripper_cmd: bool = False
    shift_gripper_cmd: bool = False
    current_point: int = 0
    gripper_state: int = 0
    shift_gripper_state: int = 0


# state_manager.py
class StateManager:
    """Thread-safe управление состоянием робота"""

    def __init__(self):
        self._lock = threading.Lock()
        self._state = RobotState()

    def update(self, **kwargs):
        """Обновить поля состояния"""
        with self._lock:
            valid_fields = {field_obj.name for field_obj in dataclasses.fields(self._state)}
            for key, value in kwargs.items():
                if key not in valid_fields:
                    raise KeyError(f"Unknown state field: {key}")
                setattr(self._state, key, value)

    def get_snapshot(self) -> RobotState:
        """Получить копию текущего состояния"""
        with self._lock:
            return RobotState(**self._state.__dict__)

    def get_field(self, field_name: str):
        """Получить значение одного поля"""
        with self._lock:
            return getattr(self._state, field_name)


# data_manager.py
class DataManager:
    """Управление waypoints и trajectories"""

    def __init__(self, points_path: Path, traj_path: Path, actions_dict: dict, logger):
        self.points_path = points_path
        self.traj_path = traj_path
        self.log = logger
        self.waypoints: Dict[str, Dict] = {}
        self.trajectories: Dict[str, Dict] = {}
        self.actions = actions_dict

    def load_waypoints(self) -> Dict[str, Dict]:
        """Загрузить waypoints из файла"""
        try:
            with open(self.points_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.waypoints = {wp['name']: wp for wp in data['waypoints']}
                return self.waypoints
        except Exception as e:
            self.log.warning(f"Error loading waypoints: {e}")
            return {}

    def load_trajectories(self) -> Dict[str, Dict]:
        """Загрузить trajectories из файла"""
        try:
            with open(self.traj_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.trajectories = {traj['name']: traj for traj in data['trajectories']}
                return self.trajectories
        except Exception as e:
            self.log.warning(f"Error loading trajectories: {e}")
            return {}

    def get_waypoint(self, name: str) -> Dict:
        """Получить waypoint по имени"""
        if name not in self.waypoints:
            raise ValueError(f"Waypoint '{name}' not found")
        return self.waypoints[name]

    def get_tcp_pose(self, waypoint_name: str) -> List[float]:
        """Получить TCP позицию из waypoint"""
        wp = self.get_waypoint(waypoint_name)
        pos = wp['tcp']
        return [pos['x'], pos['y'], pos['z'], pos['Rx'], pos['Ry'], pos['Rz']]

    def get_joint_pose(self, waypoint_name: str) -> List[float]:
        """Получить углы суставов из waypoint"""
        wp = self.get_waypoint(waypoint_name)
        joints = wp['joints']
        return [joints['J1'], joints['J2'], joints['J3'],
                joints['J4'], joints['J5'], joints['J6']]

    def get_move_params(self, waypoint_name: str) -> Dict[str, float]:
        """Получить параметры движения из waypoint"""
        wp = self.get_waypoint(waypoint_name)
        return {
            'speed': float(wp['speed']),
            'accel': float(wp['accel']),
            'blend': float(wp['blend'])
        }


# motion_controller.py
class MotionController:
    """Управление движением робота"""

    def __init__(self, robot_api, data_manager, logger):
        self.robot = robot_api
        self.data = data_manager
        self.log = logger

    @staticmethod
    def normalize_ratio(value) -> float:
        """Нормализует значение в диапазон [0.0, 1.0]"""
        try:
            float_val = float(value)
        except Exception:
            return 0.0

        if math.isnan(float_val) or math.isinf(float_val):
            return 0.0
        return max(0.0, min(1.0, float_val))

    def add_waypoint_line(self, tcp_pose: List[float],
                          speed: float, accel: float, blend: float):
        """Добавить waypoint для линейного движения (ОРИГИНАЛЬНЫЙ МЕТОД)"""
        n_speed = self.normalize_ratio(speed)
        n_accel = self.normalize_ratio(accel)

        if n_speed != speed or n_accel != accel:
            self.log.debug(
                f"Line motion params normalized: "
                f"speed {speed}→{n_speed}, accel {accel}→{n_accel}"
            )

        self.robot.motion.linear.add_new_waypoint(
            tcp_pose=tcp_pose,
            speed=n_speed,
            accel=n_accel,
            blend=blend,
            orientation_units='deg'
        )

    def add_waypoint_joint(self, angle_pose: List[float],
                           speed: float, accel: float, blend: float):
        """Добавить waypoint для движения по суставам (ОРИГИНАЛЬНЫЙ МЕТОД)"""
        self.robot.motion.joint.add_new_waypoint(
            angle_pose=angle_pose,
            speed=speed,
            accel=accel,
            blend=blend,
            units='deg'
        )

    def wait_motion_complete(self, await_sec: int = -1) -> bool:
        """Ждать завершения движения (ОРИГИНАЛЬНОЕ ИМЯ МЕТОДА)"""
        try:
            return self.robot.motion.wait_waypoint_completion(0, await_sec=await_sec)
        except Exception as e:
            self.log.error(f"wait motion complete failed: {e}")
            return False


# io_controller.py
class IOController:
    """Управление цифровыми входами/выходами"""

    def __init__(self, robot_api, logger, num_outputs: int):
        self.robot = robot_api
        self.log = logger
        self.num_outputs = num_outputs

    def control_digital_outputs(self, index: int, value: bool) -> bool:
        """Управление цифровым выходом"""
        if not 0 <= index < self.num_outputs:
            self.log.error(f"Invalid output index: {index}")
            return False

        try:
            return self.robot.io.digital.set_output(index=index, value=value)
        except Exception as e:
            self.log.error(f"Error setting output {index}: {e}")
            return False


# telemetry_monitor.py
class TelemetryMonitor:
    """Мониторинг телеметрии"""

    def __init__(self, robot_api, state_manager, logger):
        self.robot = robot_api
        self.state = state_manager
        self.log = logger

    def update(self):
        """Обновить телеметрию"""
        try:
            tcp = self.robot.motion.linear.get_actual_position()
            joints = self.robot.motion.joint.get_actual_position()
            mode = self.robot.motion.mode.get()

            self.state.update(
                tcp_position=list(tcp),
                joint_position=list(joints),
                mode=mode
            )
        except Exception as e:
            self.state.update(last_error=str(e))
            self.log.debug(f"Telemetry error: {e}")

    def check_controller_state(self):
        """Проверить состояние контроллера"""
        try:
            safety = self.robot.safety_status.get()
            ctrl = self.robot.controller_state.get()

            self.state.update(
                safety_status=safety,
                controller_state=ctrl
            )

            if safety == Iss.fault.name or ctrl == Ics.failure.name:
                self.log.error("Manipulator Error (fault/failure)")
        except Exception as e:
            self.state.update(last_error=LastError.err_check_state)
            self.log.error(f"CheckControllerState error: {e}")


# robot_controller.py
class RobotController:
    """Главный контроллер робота"""

    def __init__(self, robot_ip: str, cmd_queue: Queue, logger, heartbeat_cb=None):
        self.log = logger
        self.cmd_queue = cmd_queue
        self.stop_event = threading.Event()
        self._heartbeat_cb = heartbeat_cb

        # Раскомментить для отладки с манипулятором по месту
        # Robot API
        # try:
        #     self.Robot = RobotApi(robot_ip, show_std_traceback=True)
        # except VersionError as e:
        #     self.log.critical(f"Robot API version mismatch: {e}")
        #     raise

        # Компоненты
        self.state = StateManager()
        self.data = DataManager(POINTS_PATH, TRAJ_PATH, actions, logger)
        # Раскомментить для отладки с манипулятором по месту
        # self.mc = MotionController(self.Robot, self.data, logger)
        # self.io = IOController(self.Robot, logger, NUM_DIGITAL_IO)
        # self.telemetry = TelemetryMonitor(self.Robot, self.state, logger)

        # Загрузка
        self.data.load_waypoints()
        self.data.load_trajectories()

        # Состояние для joystick
        self._joystick_running = False
        self._joystick_thread = None
        self._nearest_info = None
        self._nearest_boot_done = False

    # ---------- Публичные методы (используемые извне) ----------

    def get_state_snapshot(self) -> RobotState:
        return self.state.get_snapshot()

    def get_waypoints_snapshot(self) -> dict:
        return dict(self.data.waypoints)

    def get_trajectories_snapshot(self) -> dict:
        return dict(self.data.trajectories)

    def get_actions_snapshot(self) -> dict:
        return dict(self.data.actions)

    def get_current_tcp_position(self) -> List[float]:
        return self.state.get_field('tcp_position')

    def get_current_joint_position(self) -> List[float]:
        return self.state.get_field('joint_position')

    def get_controller_state(self) -> str:
        return self.state.get_field('controller_state')

    def get_nearest_info(self):
        return self._nearest_info or None

    # ---------- Управление режимами ----------

    def manipulator_power_control(self, power_on: int) -> None:
        """Управление питанием манипулятора"""
        try:
            if power_on == 0:
                # self.Robot.controller_state.set('off', await_sec=10)
                self.Robot.controller_state.set(str(ControllerState.off.name), await_sec=10)
                self.state.update(powered=False, last_command="PowerOff")
                self.log.info("Manipulator deactivated")
            elif power_on == 1:
                self.run_controller()
                self.state.update(powered=True, last_command="PowerOn")
                self.log.info("Manipulator powered")
            else:
                self.log.warning(f"Unknown power command: {power_on}")
        except FunctionTimeOutError as e:
            self.state.update(last_error=LastError.err_switching_power_state)
            self.log.error(f"Timeout switching power state: {e}")
        except Exception as e:
            self.state.update(last_error=LastError.err_power_control)
            self.log.error(f"Error in power control: {e}")

    def manipulator_stop_drive(self) -> None:
        """Остановка движения"""
        try:
            # self.Robot.motion.mode.set('hold')
            self.Robot.motion.mode.set(str(MotionMode.hold.name))
        except Exception as e:
            self.state.update(last_error=LastError.err_switching_stop_mode)
            self.log.error(f"Stop Mode Switching Error: {e}")

    def manipulator_free_drive(self, free_drive: int) -> None:
        """Режим свободного движения"""
        try:
            if free_drive == 1:
                self.log.info("Activating Zero Gravity Mode")
                self.Robot.motion.free_drive()
                self.state.update(free_drive=True, mode='hold')
            elif free_drive == 0:
                self.log.info("Deactivating Zero Gravity Mode")
                # self.Robot.motion.mode.set('hold')
                self.Robot.motion.mode.set(str(MotionMode.hold.name))
                self.state.update(free_drive=False, mode='hold')
            else:
                self.log.warning(f"Unknown free drive command: {free_drive}")
        except Exception as e:
            self.state.update(last_error=LastError.err_switching_zero_gravity)
            self.log.error(f"Zero Gravity Mode Switching Error: {e}")

    def run_controller(self):
        """Запуск контроллера в режим RUN"""
        try:
            # if self.Robot.controller_state.get() != 'run':
            if self.Robot.controller_state.get() != str(ControllerState.run.name):
                # self.Robot.controller_state.set('off', await_sec=1)
                self.Robot.controller_state.set(str(ControllerState.off.name), await_sec=1)
                # self.Robot.controller_state.set('run', await_sec=10)
                self.Robot.controller_state.set(str(ControllerState.run.name), await_sec=10)
        except Exception as e:
            self.state.update(last_error=LastError.err_switching_run_mode)
            self.log.error(f"Run Mode Switching Error: {e}")

    # ---------- Движение ----------

    def move_to_point(self, point_name: str, motion: str = 'line') -> None:
        """Движение к точке по имени"""
        if point_name not in self.data.waypoints:
            raise ValueError(f"Waypoint {point_name} not found")

        tcp_pose = self.data.get_tcp_pose(point_name)
        joint_pose = self.data.get_joint_pose(point_name)
        params = self.data.get_move_params(point_name)

        if motion == 'joint':
            self.mc.add_waypoint_joint(
                joint_pose,
                params['speed'],
                params['accel'],
                params['blend']
            )
        else:
            self.mc.add_waypoint_line(
                tcp_pose,
                params['speed'] / 100,
                params['accel'] / 100,
                params['blend'] / 100
            )

        # self.Robot.motion.mode.set(MotionMode.move)
        self.Robot.motion.mode.set("move")
        self.state.update(mode='move', last_command=f"MoveToPoint:{point_name}")
        self.log.info(f"Moving to point '{point_name}'")

    def execute_trajectory(self, trajectory: RobotTrajectories) -> None:
        """Выполнить траекторию"""
        self.state.update(last_error=0)
        print(self.state.get_field('controller_state'))
        if self.state.get_field('controller_state') != 'run':
            self.state.update(
                trajectory_state=trajectory.value + BLOCK,
                last_error=LastError.err_not_ready
            )
            self.log.error("Trajectory rejected: manipulator not in run state")
            return

        try:
            if trajectory.name not in self.data.trajectories:
                raise ValueError(f"No trajectory mapped for {trajectory}")

            nearest_point = self.find_nearest_waypoint()
            nearest_wp = nearest_point.get("waypoint")

            self.exec_available_trajectory(nearest_wp, trajectory)

        except FunctionTimeOutError as e:
            self.state.update(last_error=LastError.err_timeout_trajectory)
            self.log.error(f"Timeout executing trajectory: {e}")
        except Exception as e:
            self.state.update(last_error=LastError.err_common_trajectory)
            self.log.error(f"EXECUTE_TRAJECTORY failed: {e}")

    def exec_available_trajectory(self, nearest_wp, trajectory) -> None:
        """Выполнить доступную траекторию"""
        wp_available = True  # commissioning
        if wp_available:  # trajectory.name in available_trajectories.get(nearest_wp) # commissioning
            for position in self.data.trajectories[trajectory.name]['positions']:
                self.cmd_queue.put(
                    Command(
                        CmdType.MOVE_TO_POINT,
                        {"name": position.get("name"), "motion": "joint"},
                        source="GUI"
                    )
                )

            # self.Robot.motion.mode.set(MotionMode.move)
            self.Robot.motion.mode.set('move')
            # self.state.update(mode='move', last_command=trajectory.name)
            self.log.info(f"Executing trajectory: {trajectory.name}")

            if trajectory:
                self.state.update(trajectory_state=trajectory.value + EXECUTION)

            finish_motion = self.mc.wait_motion_complete(await_sec=-1)
            if trajectory and finish_motion:
                self.state.update(trajectory_state=trajectory.value + FINISHED)
        else:
            self.state.update(
                trajectory_state=trajectory.value + BLOCK,
                last_error=LastError.err_choose_trajectory
            )
            self.log.error("Can't move by selected trajectory from current point!")

    def execute_action(self, action: RobotActions) -> None:
        """Выполнить действие"""
        self.state.update(last_error=0)
        if self.state.get_field('controller_state') != 'run':
            self.state.update(
                action_state=action.value + BLOCK,
                last_error=LastError.err_not_ready
            )
            self.log.error("Action rejected: manipulator ot in run state")
            return

        try:
            if action.name not in self.data.actions:
                raise ValueError(f"No Action mapped for {action}")
            else:
                self.log.info(f"Executing action: {action.name}")

                if action:
                    self.state.update(action_state=action.value + EXECUTION)

                finish_motion = self.mc.wait_motion_complete(await_sec=-1)

                for command in self.data.actions.get(action.name).commands:
                    if command.cmd_type == EXEC_TRAJ and finish_motion:
                        # self.cmd_queue.put(Command(
                        #     CmdType.EXECUTE_TRAJECTORY,
                        #     {'num': int(getattr(RobotTrajectories, command.name).value)},
                        #     source="GUI"
                        # ))
                        self.execute_trajectory(getattr(RobotTrajectories, command.name))

                    if command.cmd_type == GRIPPER_CMD and finish_motion:
                        self.cmd_queue.put(Command(
                            CmdType.GRIPPER_CMD,
                            {'index': GRIPPER_DO_INDEX, 'value': bool(command.name)},
                            source="GUI"
                        ))
                    # if command.cmd_type == "PLC_COM":
                    #     pass

                finish_motion = self.mc.wait_motion_complete(await_sec=-1)
                if action and finish_motion:
                    self.state.update(action_state=action.value + FINISHED)

        except FunctionTimeOutError as e:
            self.state.update(action_state=action.value + EXCEPTION,
                              last_error=LastError.err_timeout_action)
            self.log.error(f"Timeout executing action: {e}")
        except Exception as e:
            self.state.update(action_state=action.value + EXCEPTION,
                              last_error=LastError.err_common_action)
            self.log.error(f"EXECUTE_ACTION failed: {e}")

    # ---------- Грипперы ----------
    def execute_gripper(self, clamp: bool) -> None:
        """Выполнение основной команды Гриппера"""
        self.state.update(last_error=0)

        if self.state.get_field('controller_state') != 'run':
            self.state.update(
                gripper_state=BLOCK,
                last_error=LastError.err_not_ready
            )
            self.log.error("Gripper command rejected: manipulator not in run state")
            return

        try:
            self.state.update(gripper_state=EXECUTION)

            success = self.io.control_digital_outputs(GRIPPER_DO_INDEX, clamp)

            if success:
                self.state.update(gripper_cmd=clamp, gripper_state=FINISHED)
                self.log.info(f"Gripper: {'CLAMPED' if clamp else 'RELEASED'}")
            else:
                self.state.update(gripper_state=EXCEPTION, last_error=LastError.err_gripper_cmd)
                self.log.error("Failed to execute gripper command")

        except Exception as e:
            self.state.update(gripper_state=EXCEPTION, last_error=LastError.err_gripper_cmd)
            self.log.error(f"Error executing gripper command: {e}")

    def execute_shift_gripper(self, shift: bool) -> None:
        """Выполнить команду смены Гриппера"""
        self.state.update(last_error=0)

        if self.state.get_field('controller_state') != 'run':
            self.state.update(
                shift_gripper_state=BLOCK,
                last_error=LastError.err_not_ready
            )
            self.log.error("Shift gripper command rejected: manipulator not in run state")
            return

        # Дополнительная проверка безопасности для замены
        if shift and not self.state.get_field('gripper_cmd'):
            # self.log.warning("Attempting to shift gripper while gripper is open")
            # # Можно либо заблокировать, либо позволить - зависит от требований
            pass

        try:
            self.state.update(shift_gripper_state=EXECUTION)

            success = self.io.control_digital_outputs(SHIFT_GRIPPER_DO_INDEX, shift)

            if success:
                self.state.update(shift_gripper_cmd=shift, shift_gripper_state=FINISHED)
                self.log.info(f"Shift gripper: {'SHIFTED' if shift else 'NOT SHIFTED'}")
            else:
                self.state.update(shift_gripper_state=EXCEPTION, last_error=LastError.err_shift_gripper_cmd)
                self.log.error("Failed to execute shift gripper command")

        except Exception as e:
            self.state.update(shift_gripper_state=EXCEPTION, last_error=LastError.err_shift_gripper_cmd)
            self.log.error(f"Error executing shift gripper command: {e}")

    # ---------- Утилиты ----------

    def find_nearest_waypoint(self) -> dict:
        """Найти ближайший waypoint"""
        current_tcp = self.get_current_tcp_position()

        self.data.load_waypoints()
        self.data.load_trajectories()

        best_name = None
        best_dist = float("inf")

        for name, wp in self.data.waypoints.items():
            tcp = wp.get("tcp")
            dist = math.sqrt(
                (current_tcp[0] - float(tcp["x"])) ** 2 +
                (current_tcp[1] - float(tcp["y"])) ** 2 +
                (current_tcp[2] - float(tcp["z"])) ** 2
            )
            if dist < best_dist:
                best_dist, best_name = dist, name

        try:
            self.state.update(current_point=getattr(RobotPoints, best_name).value)
        except AttributeError:
            print('Trajectory not found')

        if best_name is None:
            info = {"waypoint": "", "distance": 0.0, "trajectories": []}
            self._nearest_info = info
            return info

        traj_list = []
        for traj_name, traj in self.data.trajectories.items():
            for entry in traj.get("positions", []):
                if entry.get("name") == best_name:
                    traj_list.append(traj_name)
                    break

        info = {"waypoint": best_name, "distance": best_dist, "trajectories": traj_list}
        self._nearest_info = info
        # self.log.info(
        #     f"Nearest waypoint: {best_name}; "
        #     f"distance={best_dist:.3f}; trajectories={traj_list}"
        # )
        return info

    def _joystick_worker(self, coord_sys=None) -> None:
        """Worker для simple joystick"""
        self._joystick_running = True
        self.log.info("simple joystick started")
        try:
            if coord_sys is None:
                self.Robot.motion.simple_joystick()
            else:
                self.Robot.motion.simple_joystick(coordinate_system=coord_sys)
        except Exception as e:
            self.state.update(last_error=LastError.err_sj_activation)
            self.log.error(f"Error Simple Joystick activation: {e}")
        finally:
            self._joystick_running = False
            self.log.info("Simple joystick finished")

    def start_simple_joystick(self, coord_sys=None) -> None:
        """Запустить simple joystick"""
        if self._joystick_running and \
                self._joystick_thread and self._joystick_thread.is_alive():
            self.log.info("Simple joystick already running")
            return

        # self.run_controller()

        self._joystick_thread = threading.Thread(
            target=self._joystick_worker,
            args=(coord_sys,),
            name="SimpleJoystickThread",
            daemon=True
        )
        self._joystick_thread.start()

    # ---------- Главный цикл ----------

    def run(self) -> None:
        """Главный цикл контроллера"""
        self.log.info(f"RobotController started [PORT_TYPE={PORT_TYPE}]")

        while not self.stop_event.is_set():
            try:
                # Мониторинг
                # Раскомментить для отладки с манипулятором по месту
                # self.telemetry.check_controller_state()
                # self.telemetry.update()

                if self._heartbeat_cb:
                    try:
                        self._heartbeat_cb('rc')
                    except Exception:
                        pass

                # Получение команды
                try:
                    cmd: Command = self.cmd_queue.get(timeout=0.1)
                except Empty:
                    if not self._nearest_boot_done:
                        try:
                            self.find_nearest_waypoint()
                        except Exception as e:
                            self.log.exception(f"Initial nearest calc failed: {e}")
                        finally:
                            self._nearest_boot_done = True
                            self.log.warning(f"_nearest_boot_done {self._nearest_boot_done}")
                    continue

                # ОБРАБОТКА КОМАНД
                if cmd.type == CmdType.POWER:
                    self.manipulator_power_control(cmd.payload['state'])

                elif cmd.type == CmdType.FREE_DRIVE:
                    self.manipulator_free_drive(cmd.payload['state'])

                elif cmd.type == CmdType.EXECUTE_TRAJECTORY:
                    self.data.load_waypoints()
                    self.execute_trajectory(RobotTrajectories(cmd.payload['num']))

                elif cmd.type == CmdType.EXECUTE_ACTION:
                    self.execute_action(RobotActions(cmd.payload['num']))

                elif cmd.type == CmdType.MOVE_TO_POINT:
                    self.data.load_waypoints()
                    motion = cmd.payload.get('motion', 'line')
                    self.move_to_point(cmd.payload['name'], motion)

                elif cmd.type == CmdType.GRIPPER_CMD:
                    index = cmd.payload['index']
                    value = bool(cmd.payload['value'])
                    if index == GRIPPER_DO_INDEX:
                        self.execute_gripper(value)
                    elif index == SHIFT_GRIPPER_DO_INDEX:
                        self.execute_shift_gripper(value)
                    else:
                        self.log.warning(f"Unknown gripper index: {index}")

                elif cmd.type == CmdType.REFRESH_WAYPOINTS:
                    self.data.load_waypoints()

                elif cmd.type == CmdType.STOP_MOVE:
                    self.manipulator_stop_drive()

                elif cmd.type == CmdType.FIND_NEAREST:
                    self.find_nearest_waypoint()

                elif cmd.type == CmdType.START_SIMPLE_JOYSTICK:
                    self.start_simple_joystick(cmd.payload.get('coord_sys'))

                elif cmd.type == CmdType.SHUTDOWN:
                    self.log.info("Shutdown command received")
                    break

                else:
                    self.log.warning(f"Unknown command type: {cmd.type}")

            except Exception as e:
                self.state.update(last_error=LastError.err_rc_loop)
                self.log.exception(f"Unhandled error in loop: {e}")

        self.log.info("RobotController stopped")

    def stop(self) -> None:
        """Остановка контроллера"""
        self.stop_event.set()
