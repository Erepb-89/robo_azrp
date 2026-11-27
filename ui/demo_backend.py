"""Offline-only simulation of engineer controls. Never imports robot I/O."""
from types import SimpleNamespace


class _DynamicNames:
    def __getattr__(self, name):
        # For Digital Outputs, return the port name; for SIM_DI false by default.
        return name


class _SimInputs:
    def __getattr__(self, name):
        return False


class _SimIO:
    def __init__(self):
        self.outputs = {}

    def set_do(self, output, state):
        self.outputs[output] = bool(state)

    def get_do(self, output):
        return self.outputs.get(output, False)


class _SimLedState:
    def __init__(self):
        self.pattern = "OFF"

    def set_pattern(self, pattern):
        self.pattern = pattern


class _SimController:
    def __init__(self):
        self.io = _SimIO()
        self.led_state = _SimLedState()


def make_demo_engineering_backend():
    pattern_names = (
        "OFF", "GREEN_SOLID", "GREEN_BLINK", "YELLOW_SOLID", "YELLOW_BLINK",
        "RED_SOLID", "RED_BLINK"
    )
    patterns = SimpleNamespace(**{name: name for name in pattern_names})
    return _SimController(), _DynamicNames(), _SimInputs(), _SimInputs(), patterns
