import enum
from dataclasses import dataclass
from enum import Enum, auto
from typing import Dict, Any, Optional


class CmdType(Enum):
    POWER = auto()  # {'state': False/True}
    FREE_DRIVE = auto()  # {'state': 0|1}
    EXECUTE_TRAJECTORY = auto()  # {'num': int}
    EXECUTE_ACTION = auto()  # {'num': int}
    MOVE_TO_POINT = auto()  # {'name': str}
    GRIPPER_CMD = auto()  # {'index': int, 'value': bool}
    REFRESH_WAYPOINTS = auto()
    STOP_MOVE = auto()
    PAUSE = auto()
    SHUTDOWN = auto()
    FIND_NEAREST = auto()
    START_SIMPLE_JOYSTICK = auto()
    MOTION_DONE = auto()  # физ. остановка движения {'ok': bool, 'gen': int}


@dataclass
class Command:
    type: CmdType
    payload: Dict[str, Any] | None = None
    source: Optional[str] = None


class RobotPoints(enum.Enum):
    BGIntP010 = 0
    BGIntP011 = 100
    BGM1P010 = 200
    BGM1P015 = 300
    BGM1P020 = 400
    BAM1P010 = 500
    BAM1P015 = 600
    EAM1P000 = 700
    EAM1P010 = 800
    EAM1P020 = 900
    EAM1P030 = 1000
    EAM1P040 = 1100
    BG2M1P010 = 1200
    EG2M1P010 = 1300
    EG2M1P020 = 1400
    BG1M1P010 = 1500
    EG1M1P010 = 1600
    EG1M1P020 = 1700
    EG1M1P030 = 1800
    EG1M1P040 = 1900
    BG2IntP010 = 2000
    BGM2P010 = 2100
    BGM2P015 = 2200
    BGM2P020 = 2300
    BAM2P010 = 2400
    BAM2P015 = 2500
    EAM2P000 = 2600
    EAM2P010 = 2700
    EAM2P020 = 2800
    EAM2P030 = 2900
    EAM2P040 = 3000
    BG2M2P010 = 3100
    EG2M2P010 = 3200
    EG2M2P020 = 3300
    BG1M2P010 = 3400
    EG1M2P010 = 3500
    EG1M2P020 = 3600
    EG1M2P030 = 3700
    EG1M2P040 = 3800
    BG1IntP001 = 3900
    BG1IntP010 = 4000


class RobotTrajectories(enum.Enum):
    tBGIntP010_To_BGIntP011 = 1
    tBGIntP010_To_BG1IntP001 = 2
    tBGIntP010_To_BG1IntP010 = 3
    tBG1IntP010_To_XXX = 4
    tBGIntP010_To_BGM1P020 = 5
    tBGM1P020_To_BGIntP010 = 6
    tBGIntP010_To_BGM2P020 = 7
    tBGM2P020_To_BGIntP010 = 8
    tBGM1P020_To_BAM1P015 = 9
    tBAM1P015_To_EAM1P000 = 10
    tEAM1P000_To_EAM1P040 = 11
    tEAM1P000_To_BGM1P015 = 12
    tBAM1P015_To_BGM1P020 = 13
    tBGM1P020_To_BG2M1P010 = 14
    tBG2M1P010_To_EG2M1P010 = 15
    tEG2M1P010_To_EG2M1P020 = 16
    tEG2M1P010_To_BG2M1P010 = 17
    tBG2M1P010_To_BGM1P020 = 18
    tBGM1P020_To_BG1M1P010 = 19
    tBG1M1P010_To_EG1M1P010 = 20
    tEG1M1P010_To_EG1M1P040 = 21
    tEG1M1P010_To_BG1M1P010 = 22
    tBG1M1P010_To_BGM1P020 = 23
    tBGIntP010_To_BG2IntP010 = 24
    tBG2IntP010_To_XXX = 25
    tBGM2P020_To_BAM2P015 = 26
    tBAM2P015_To_EAM2P000 = 27
    tEAM2P000_To_EAM2P040 = 28
    tEAM2P000_To_BAM2P015 = 29
    tBAM2P015_To_BGM2P020 = 30
    tBGM2P020_To_BG2M2P010 = 31
    tBG2M2P010_To_EG2M2P010 = 32
    tEG2M2P010_To_EG2M2P020 = 33
    tEG2M2P010_To_BG2M2P010 = 34
    tBG2M2P010_To_BGM2P020 = 35
    tBGM2P020_To_BG1M2P010 = 36
    tBG1M2P010_To_EG1M2P010 = 37
    tEG1M2P010_To_EG1M2P040 = 38
    tEG1M2P010_To_BG1M2P010 = 39
    tBG1M2P010_To_BGM2P020 = 40


class RobotActions(enum.Enum):
    aBGIntP010_To_BGIntP011 = 1
