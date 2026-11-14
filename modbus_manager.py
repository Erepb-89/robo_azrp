import threading
import time
from logging import Logger

from pymodbus import FramerType
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

from config import RETRIES, SERVER_HOST, SERVER_PORT, POLL_INTERVAL, PORT, SLAVE_ID, RED_HOLDING, GREEN_HOLDING, \
    PERIOD_S, DUTY


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
        with self.client:
            try:
                self.client.connect()
                print("Соединение открыто")

            except ModbusException as e:
                # self.logger.error(f"Error in Modbus RTU handler loop: {e}")
                print(f"Произошла ошибка Modbus: {e}")
            except Exception as e:
                # self.logger.error(f"Error in Modbus RTU handler: {e}")
                print(f"Произошла другая ошибка: {e}")
            finally:
                self.client.close()
                print("Соединение закрыто")

            if self.heartbeat_cb:
                try:
                    self.heartbeat_cb('modbus RTU')
                except Exception:
                    pass

    def stop(self) -> None:
        self.stop_event.set()

class Blinker:
    def __init__(self, client):
        self.client = client
        self.blinking = True

    def write_coils(self, address, values):
        return self.client.write_coils(address, values, device_id=SLAVE_ID)

    def write_holdings(self, address, values):
        return self.client.write_registers(address, values, device_id=SLAVE_ID)

    def stop_blinking(self):
        self.blinking = False
        self.write_coils(9, [0])
        self.write_holdings(RED_HOLDING, [0, 0, 0])

    def green_light(self):
        self.write_coils(9, [1])
        self.write_holdings(GREEN_HOLDING, [128])

    def start_blinking(self, state, color):
        val = [128] if state else [0]
        holding_color = GREEN_HOLDING
        if color == 'G':
            holding_color = GREEN_HOLDING
        elif color == 'Y' and state == False:
            holding_color = RED_HOLDING
            val = [0, 0]
        elif color == 'Y' and state == True:
            holding_color = RED_HOLDING
            val = [128, 128]
        elif color == 'R':
            holding_color = RED_HOLDING

        self.write_holdings(holding_color, val)

    def blink(self, color):
        state = True
        self.write_coils(9, [1])

        try:
            while self.blinking:
                try:
                    self.start_blinking(state, color)
                except (ModbusException, OSError) as exc:
                    print(f"Ошибка обмена: {exc}")

                time.sleep(PERIOD_S * (DUTY if state else 1 - DUTY))
                state = not state
        except KeyboardInterrupt:
            pass
        finally:
            try:
                self.stop_blinking()
            except (ModbusException, OSError):
                pass
            self.client.close()
            print("\nВыходы выключены, соединение закрыто")

# if __name__ == "__main__":
# tcp_manager = ModbusTCPManager()
# tcp_manager.run_sync_client()

# rtu_manager = ModbusRTUManager()
# rtu_manager.run_sync_client()
