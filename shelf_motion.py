"""Движение для паллета: линейные перемещения и выдвижение крючком.

Робот тянет полку специальным крючком на корпусе (гриппер не задействован):
- зацеп/отвод выполняются обычными линейными переходами в заданные точки;
- вытягивание — «guarded move»: джог вдоль оси до срабатывания концевика
  DI.SHELF_n. В API готового guarded move нет, поэтому используется цикл
  motion.linear.jog_once(...) в режиме 'jog' с опросом входа.

Модуль работает поверх RobotController (rc): rc.Robot, rc.io, rc.mc,
rc.move_to_point_sync, rc.message.
"""
import time

from config import IO_POLL_SEC


def move_linear_pose_sync(rc, tcp_pose, speed, accel, blend,
                          abort_event=None) -> bool:
    """Линейное перемещение к TCP-позе с ожиданием физической остановки."""
    try:
        rc.Robot.motion.linear.add_new_waypoint(
            tcp_pose=list(tcp_pose),
            speed=speed,
            accel=accel,
            blend=blend,
            orientation_units='deg',
        )
        rc.Robot.motion.mode.set('move')
    except Exception as e:
        rc.message(f"Паллет: ошибка линейного движения: {e}", 'error')
        return False
    try:
        return rc.mc.wait_motion_stopped(abort_event=abort_event,
                                         require_motion_start=True)
    except Exception as e:
        rc.message(f"Паллет: ожидание остановки: {e}", 'error')
        return False


def move_to_named_point_sync(rc, point_name, motion='line',
                             abort_event=None) -> bool:
    """Переход в именованную точку points.json с ожиданием остановки."""
    if not point_name:
        return False
    try:
        return bool(rc.move_to_point_sync(point_name, motion, abort_event))
    except Exception as e:
        rc.message(f"Паллет: переход к точке {point_name}: {e}", 'error')
        return False


def jog_until_di(rc, di, axis, direction, timeout, abort_event=None) -> bool:
    """Выдвижение крючком: джог вдоль оси axis до срабатывания концевика di.
            jog_axis (JogAxis): Ось перемещения. Допустимые значения:
                - 'X', 'Y', 'Z' — линейные перемещения;
                - 'Rx', 'Ry', 'Rz' — угловые повороты.
            jog_direction (JogDirection): Направление движения:
                - '+' — в положительном направлении оси;
                - '-' — в отрицательном направлении оси.
    Returns:
        True — концевик сработал (полка выдвинута);
        False — таймаут/СТОП/ошибка.
    """
    if axis is None or direction is None or timeout is None:
        rc.message("Паллет: не заданы ось/направление/таймаут выдвижения",
                   'error')
        return False
    if di is None:
        rc.message("Паллет: не задан концевик выдвижения полки", 'error')
        return False

    try:
        rc.Robot.motion.linear.set_jog_param_in_tcp('base')
    except Exception as e:
        rc.message(f"Паллет: set_jog_param_in_tcp('base'): {e}", 'error')
        return False

    try:
        rc.Robot.motion.mode.set('jog')
    except Exception as e:
        rc.message(f"Паллет: включение режима 'jog': {e}", 'error')
        return False

    deadline = time.monotonic() + float(timeout)
    try:
        while True:
            if abort_event is not None and abort_event.is_set():
                rc.message("Паллет: выдвижение прервано (СТОП)", 'warning')
                return False

            # концевик уже сработал?
            try:
                if rc.io.get_di(di):
                    rc.message("Паллет: концевик выдвижения сработал")
                    return True
            except Exception as e:
                rc.message(f"Паллет: чтение концевика: {e}", 'error')
                return False

            if time.monotonic() >= deadline:
                rc.message("Паллет: таймаут концевика выдвижения", 'error')
                return False

            try:
                rc.Robot.motion.linear.jog_once(axis, direction)
            except Exception as e:
                rc.message(f"Паллет: jog_once({axis},{direction}): {e}", 'error')
                return False

            time.sleep(IO_POLL_SEC)
    finally:
        # Прекратить джог: без вызовов jog_once движение останавливается.
        try:
            rc.Robot.motion.mode.set('hold')
        except Exception:
            pass
