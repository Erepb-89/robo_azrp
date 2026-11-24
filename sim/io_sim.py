"""
Виртуальные цифровые входы/выходы для SIM-режима.

Повторяет интерфейс API.io.digital, который использует IOController:
get_input / get_output / set_output / set_input_function. Реакции станка на
DO пока не моделируются (это кусок 12); выходы просто запоминаются.
"""
import threading
from typing import List, Tuple

from API.source.models.constants import (
    CTRLR_MAX_DIG_IN_BYTES,
    CTRLR_MAX_DIG_OUT_BYTES,
)

from sim.scenario import Scenario


class SimDigitalIO:
    """Банк из N виртуальных входов и выходов."""

    def __init__(self, scenario: Scenario, count: int = 24):
        self.scenario = scenario
        self.count = count
        self._lock = threading.Lock()
        self._inputs: List[bool] = [False] * count
        self._outputs: List[bool] = [False] * count
        for index, value in scenario.resolved_inputs().items():
            if 0 <= index < count:
                self._inputs[index] = bool(value)

    # ── интерфейс API.io.digital ────────────────────────────────────────────

    def set_input_function(self, index: int, function: str) -> bool:
        return True

    def get_input(self, index: int) -> bool:
        with self._lock:
            if not 0 <= index < self.count:
                return False
            return bool(self._inputs[index])

    def get_output(self, index: int) -> bool:
        with self._lock:
            if not 0 <= index < self.count:
                return False
            return bool(self._outputs[index])

    def set_output(self, index: int, value: bool) -> bool:
        with self._lock:
            if not 0 <= index < self.count:
                return False
            self._outputs[index] = bool(value)
        return True

    # ── управление из сценариев/тестов ──────────────────────────────────────

    def set_input(self, index: int, value: bool) -> None:
        with self._lock:
            if 0 <= index < self.count:
                self._inputs[index] = bool(value)

    def snapshot(self) -> Tuple[Tuple[bool, ...], Tuple[bool, ...]]:
        with self._lock:
            return tuple(self._inputs), tuple(self._outputs)

    # ── упаковка в формат RTD ───────────────────────────────────────────────

    def dig_in_bytes(self) -> Tuple[int, ...]:
        return self._pack(self._inputs, CTRLR_MAX_DIG_IN_BYTES)

    def dig_out_bytes(self) -> Tuple[int, ...]:
        return self._pack(self._outputs, CTRLR_MAX_DIG_OUT_BYTES)

    def _pack(self, values: List[bool], size: int) -> Tuple[int, ...]:
        with self._lock:
            buf = bytearray(size)
            for index, value in enumerate(values):
                if value:
                    buf[index // 8] |= 1 << (index % 8)
            return tuple(buf)


class SimIO:
    """Хост IO: атрибут digital (как API.io)."""

    def __init__(self, scenario: Scenario, count: int = 24):
        self.digital = SimDigitalIO(scenario, count)
