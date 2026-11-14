"""Выбор и проигрывание состояния светодиодной ленты WB-LED."""
from __future__ import annotations

import threading
from enum import Enum, auto
from typing import Optional

from states_modes_errors import (
    HARDWARE_ERRORS,
    ControllerState,
    LastError,
    MachineState,
    SafetyStatus,
)


class LedPattern(Enum):
    """Паттерн индикации ленты."""
    OFF = auto()
    GREEN_SOLID = auto()
    GREEN_BLINK = auto()
    YELLOW_BLINK = auto()
    RED_BLINK = auto()


RED_CONTROLLER_STATES = {
    ControllerState.failure,
    ControllerState.force_exit,
}
RED_SAFETY_STATES = {
    SafetyStatus.fault,
    SafetyStatus.violation,
    SafetyStatus.emergency_stop,
}


def _matches(value, variants) -> bool:
    """Сравнивает значение enum/строку/число с набором enum-значений."""
    if isinstance(value, Enum):
        return value in variants
    if isinstance(value, str):
        names = {item.name for item in variants}
        values = {str(item.value) for item in variants}
        return value in names or value in values
    if isinstance(value, int):
        return value in {item.value for item in variants}
    return False


def _last_error_is_hardware(value) -> bool:
    if value is None:
        return False
    if isinstance(value, LastError):
        return value in HARDWARE_ERRORS
    if isinstance(value, int):
        return value in {item.value for item in HARDWARE_ERRORS}
    if isinstance(value, str):
        names = {item.name for item in HARDWARE_ERRORS}
        values = {str(item.value) for item in HARDWARE_ERRORS}
        return value in names or value in values
    return False


def _machine_error(state) -> bool:
    m_state = getattr(state, 'm_state', None) or {}
    return any(
        _matches(m_state.get(m), {MachineState.Error})
        for m in (1, 2)
    )


def _manipulator_error(state) -> bool:
    if _last_error_is_hardware(getattr(state, 'last_error', None)):
        return True
    if _matches(getattr(state, 'controller_state', None),
                RED_CONTROLLER_STATES):
        return True
    if _matches(getattr(state, 'safety_status', None),
                RED_SAFETY_STATES):
        return True
    return False


def _machine_manual(state) -> bool:
    signals = getattr(state, 'signals', None) or {}
    return any(
        key in signals and not signals[key]
        for key in ('M1_DoorAuto', 'M2_DoorAuto')
    )


def select_pattern(state) -> LedPattern:
    """Выбирает паттерн по приоритету: ошибка > ручной > ожидание > авто."""
    if _manipulator_error(state) or _machine_error(state):
        return LedPattern.RED_BLINK

    if (getattr(state, 'engineer_mode', False)
            or getattr(state, 'free_drive', False)
            or _machine_manual(state)):
        return LedPattern.YELLOW_BLINK

    cycle_state = getattr(state, 'cycle_state', 'idle') or 'idle'
    if cycle_state in ('waiting_start', 'waiting_resume'):
        return LedPattern.GREEN_BLINK

    if cycle_state == 'running':
        return LedPattern.GREEN_SOLID

    flags = getattr(state, 'flags', None) or {}
    if flags.get('resume_pending'):
        return LedPattern.GREEN_BLINK

    return LedPattern.OFF


class LedStateController(threading.Thread):
    """Поток, который переводит состояние робота в паттерн ленты."""

    def __init__(self, rc, led, logger, interval: float = 0.1):
        super().__init__(daemon=True, name="LedStateThread")
        self.rc = rc
        self.led = led
        self.log = logger
        self.interval = interval
        self._stop_event = threading.Event()
        self._last_pattern: Optional[LedPattern] = None

    def run(self) -> None:
        while not self._stop_event.is_set():
            try:
                state = self.rc.get_state_snapshot()
                pattern = select_pattern(state)
                if pattern is not self._last_pattern:
                    self.led.set_pattern(pattern)
                    self._last_pattern = pattern
            except Exception as exc:
                self.log.debug(f"LedStateController: {exc}")
            self._stop_event.wait(self.interval)

    def stop(self) -> None:
        self._stop_event.set()
