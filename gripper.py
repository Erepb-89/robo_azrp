"""
Грипперы G1/G2: зажим/разжатие с подтверждением по DI, перезагрузка.

WaitForGripperClamp / WaitForGripperRelax
через wait_di с тайм-аутом MAX_G_SEC.
"""
from config import MAX_G_SEC
from io_map import GRIPPER_DI
from states_modes_errors import Result, LastError


class Gripper:
    """Гриппер G (1 или 2)."""

    def __init__(self, gripper: int, rc, logger):
        self.gripper = gripper
        self.rc = rc
        self.io = rc.io
        self.log = logger

    def _di(self, role: str):
        return GRIPPER_DI[self.gripper][role]

    def clamp(self, abort=None) -> Result:
        """DO G_Clamp=true + подтверждение по DI Clamped."""
        if not self.io.gripper_do(self.gripper, True):
            return Result.Error
        if not self.io.wait_di(self._di('Clamped'), True, MAX_G_SEC, abort):
            self.rc.state.update(last_error=LastError.err_gripper_not_clamped)
            self.rc.message(f"Гриппер {self.gripper} не зажался", 'error')
            return Result.Error
        self.rc.state.update(gripper_cmd=True,
                             **{f"gripper{self.gripper}_state": 200})
        return Result.NoError

    def release(self, abort=None) -> Result:
        """DO G_Clamp=false + подтверждение по DI Relax."""
        if not self.io.gripper_do(self.gripper, False):
            return Result.Error
        if not self.io.wait_di(self._di('Relax'), True, MAX_G_SEC, abort):
            self.rc.state.update(last_error=LastError.err_gripper_not_relaxed)
            self.rc.message(f"Гриппер {self.gripper} не разжался", 'error')
            return Result.Error
        self.rc.state.update(gripper_cmd=False,
                             **{f"gripper{self.gripper}_state": 200})
        return Result.NoError

    def reset(self, abort=None) -> Result:
        """ResetGripper(G): перезагрузка гриппера — разжать и зажать."""
        if self.release(abort) != Result.NoError:
            return Result.Error
        return self.clamp(abort)