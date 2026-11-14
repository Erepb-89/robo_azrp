import threading
import time
from logging import Logger

from pymodbus import FramerType
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

from config import (RETRIES, SERVER_HOST, SERVER_PORT, POLL_INTERVAL, PORT,
                    SLAVE_ID, RED_HOLDING, PERIOD_S, DUTY,
                    LED_RGB_BRIGHTNESS, GREEN_LED, YELLOW_LED, RED_LED)
from led_control import LedPattern


class ModbusTCPManager:
    def __init__(self, logger, heartbeat_cb=None):
        self.logger = None
        self.logger = logger
        self.heartbeat_cb = heartbeat_cb
        self.stop_event = threading.Event()

    def run_sync_client(self):
        # Создаем объект клиента
        client = ModbusTcpClient(SERVER_HOST,
                                 port=SERVER_PORT,
                                 retries=RETRIES)

        # Устанавливаем соединение
        if not client.connect():
            print(f"Не удалось подключиться к {SERVER_HOST}:{SERVER_PORT}")
            return

        while True:
            # Фиксируем время начала цикла
            start_time = time.monotonic()
            try:
                # 1. Чтение Discrete Inputs — адрес 0, количество 16
                reg_result = client.read_discrete_inputs(address=0, count=16, device_id=1)
                if not reg_result.isError():
                    print(f"Значения регистров TCP: {reg_result.bits}")
                else:
                    print(f"Ошибка чтения регистров TCP: {reg_result}")

            except ModbusException as e:
                print(f"Error in Modbus TCP handler loop: {e}")
                self.logger.error(f"Error in Modbus TCP handler loop: {e}")

            if self.heartbeat_cb:
                try:
                    self.heartbeat_cb('modbus TCP')
                except Exception:
                    pass

            elapsed = time.monotonic() - start_time
            sleep_time = max(0.0, POLL_INTERVAL - elapsed)
            time.sleep(sleep_time)

    def stop(self) -> None:
        self.stop_event.set()

class ModbusRTUManager:
    def __init__(self, logger, heartbeat_cb=None):
        self.logger = None
        self.logger = logger
        self.heartbeat_cb = heartbeat_cb
        self.stop_event = threading.Event()
        # Создаем объект клиента
        self.client = ModbusSerialClient(framer=FramerType.RTU,
                                         port='/dev/ttyUSB0',
                                         baudrate=9600,
                                         parity='N',
                                         bytesize=8,
                                         stopbits=2,
                                         retries=RETRIES,
                                         timeout=0.5)

    def run_sync_client(self):
        try:
            if not self.client.connect():
                self.logger.error("Не удалось открыть Modbus RTU")
                return
            print("Соединение открыто")
            while not self.stop_event.wait(1.0):
                if self.heartbeat_cb:
                    try:
                        self.heartbeat_cb('modbus RTU')
                    except Exception:
                        pass
        except ModbusException as e:
            self.logger.error(f"Ошибка Modbus RTU: {e}")
        except Exception as e:
            self.logger.error(f"Ошибка Modbus RTU: {e}")
        finally:
            self.client.close()
            print("Соединение закрыто")

    def stop(self) -> None:
        self.stop_event.set()

class Blinker:
    """Неблокирующее мигание WB-LED"""

    def __init__(self, client, logger=None):
        self.client = client
        self.log = logger
        self._io_lock = threading.RLock()
        self._state_lock = threading.Lock()
        self._color = GREEN_LED
        self._blinking = False
        self._enabled = False
        self._wake = threading.Event()
        self._stop = threading.Event()
        self._closed = False
        self._thread = threading.Thread(
            target=self._worker, name="LedBlinkerThread", daemon=True)
        self._thread.start()

    def _log_warning(self, text: str) -> None:
        if self.log is not None:
            self.log.warning(text)
        else:
            print(text)

    def _write_coils(self, address, values):
        with self._io_lock:
            return self.client._write_coils(
                address, values, device_id=SLAVE_ID)

    def _write_holdings(self, address, values):
        with self._io_lock:
            return self.client.write_registers(
                address, values, device_id=SLAVE_ID)

    def _write_rgb(self, r: int, g: int, b: int) -> None:
        with self._io_lock:
            self._write_holdings(RED_HOLDING, [r, g, b])
            self._write_coils(9, [1 if (r or g or b) else 0])

    def start_blinking(self, state: bool, color: str) -> None:
        """Записать одну фазу: включить указанный цвет или погасить ленту."""
        color = str(color).upper()
        if color == GREEN_LED:
            rgb = (0, LED_RGB_BRIGHTNESS, 0)
        elif color == YELLOW_LED:
            rgb = (LED_RGB_BRIGHTNESS, LED_RGB_BRIGHTNESS, 0)
        elif color == RED_LED:
            rgb = (LED_RGB_BRIGHTNESS, 0, 0)
        else:
            raise ValueError(f"Неизвестный цвет WB-LED: {color!r}")

        self._write_rgb(*(rgb if state else (0, 0, 0)))

    def _set_mode(self, color: str, blinking: bool, enabled: bool) -> None:
        with self._state_lock:
            self._color = color
            self._blinking = blinking
            self._enabled = enabled
        self._wake.set()

    def stop_blinking(self) -> None:
        """Выключить ленту."""
        self._set_mode(GREEN_LED, False, False)

    def green_light(self) -> None:
        """Ровный зелёный."""
        self._set_mode(GREEN_LED, False, True)

    def blink(self, color: str) -> None:
        """Включить мигание GREEN_LED/YELLOW_LED/RED_LED без блокировки."""
        color = str(color).upper()
        if color not in (GREEN_LED, YELLOW_LED, RED_LED):
            raise ValueError(f"Неизвестный цвет WB-LED: {color!r}")
        self._set_mode(color, True, True)

    def set_pattern(self, pattern: LedPattern) -> None:
        """Совместимость с LedStateController."""
        if pattern is LedPattern.OFF:
            self.stop_blinking()
        elif pattern is LedPattern.GREEN_SOLID:
            self.green_light()
        elif pattern is LedPattern.GREEN_BLINK:
            self.blink(GREEN_LED)
        elif pattern is LedPattern.YELLOW_BLINK:
            self.blink(YELLOW_LED)
        elif pattern is LedPattern.RED_BLINK:
            self.blink(RED_LED)
        else:
            raise ValueError(f"Неизвестный паттерн WB-LED: {pattern!r}")

    def _wait(self, timeout: float) -> None:
        if self._wake.wait(timeout):
            self._wake.clear()

    def _worker(self) -> None:
        phase_on = True
        last_mode = None
        try:
            while not self._stop.is_set():
                with self._state_lock:
                    color = self._color
                    blinking = self._blinking
                    enabled = self._enabled

                mode = (color, blinking, enabled)
                if mode != last_mode:
                    last_mode = mode
                    phase_on = True

                try:
                    if not enabled:
                        self._write_rgb(0, 0, 0)
                        self._wait(1.0)
                        continue

                    if not blinking:
                        self.start_blinking(True, color)
                        self._wait(1.0)
                        continue

                    if phase_on:
                        self.start_blinking(True, color)
                        self._wait(PERIOD_S * DUTY)
                        phase_on = False
                    else:
                        self.start_blinking(False, color)
                        self._wait(PERIOD_S * (1 - DUTY))
                        phase_on = True
                except (ModbusException, OSError) as exc:
                    self._log_warning(f"WB-LED: ошибка обмена: {exc}")
                    self._wait(5)
                except Exception as exc:
                    self._log_warning(f"WB-LED: ошибка: {exc}")
                    self._wait(5)
        finally:
            try:
                self._write_rgb(0, 0, 0)
            except Exception as exc:
                self._log_warning(f"WB-LED: не удалось выключить: {exc}")

    def close(self) -> None:
        if self._closed:
            return
        self._closed = True
        self._stop.set()
        self._wake.set()
        self._thread.join(timeout=2.0)
        try:
            self.client.close()
        except Exception:
            pass


# if __name__ == "__main__":
# tcp_manager = ModbusTCPManager()
# tcp_manager.run_sync_client()

# rtu_manager = ModbusRTUManager()
# rtu_manager.run_sync_client()
