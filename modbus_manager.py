import time
from logging import Logger

from pymodbus import FramerType
from pymodbus.client import ModbusTcpClient, ModbusSerialClient
from pymodbus.exceptions import ModbusException

from config import RETRIES, SERVER_HOST, SERVER_PORT, POLL_INTERVAL


class ModbusTCPManager:
    def __init__(self, logger, heartbeat_cb=None):
        self.logger = None
        self.logger = logger
        self.heartbeat_cb = heartbeat_cb

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


class ModbusRTUManager:
    def __init__(self):  # , logger, heartbeat_cb=None):
        self.logger = None
        # self.logger = logger
        # self.heartbeat_cb = heartbeat_cb

    def run_sync_client(self):
        # Создаем объект клиента
        client = ModbusSerialClient(framer=FramerType.RTU,
                                    port='/dev/ttyUSB0',
                                    baudrate=9600,
                                    parity='N',
                                    bytesize=8,
                                    stopbits=1,
                                    retries=RETRIES,
                                    timeout=0.5)

        try:
            client.connect()
            print("Соединение открыто")

            address = 100

            # read
            rr = client.read_holding_registers(address, count=4, device_id=2)

            if rr.isError():
                print(f"Ошибка чтения: {rr.exception_code}")
            else:
                print(f"Успешно прочитано: {rr.registers}")
                print(f"Значение первого регистра: {rr.registers[0]}")
                float_values = client.convert_from_registers(rr.registers,
                                                             data_type=ModbusSerialClient.DATATYPE.FLOAT32,
                                                             word_order='little',
                                                             string_encoding=list[float])
                print(float_values)

            # write
            # write_result = client.write_register(1, value=123, device_id=2)  # Записать 123 в регистр 10
            # if write_result.isError():
            #     print(f"Ошибка записи: {write_result.exception_code}")
            # else:
            #     print("Значение записано")

            # write float
            # float_for_write = 6.784
            # float_to_regs = client.convert_to_registers(float_values,
            #                                             data_type=ModbusSerialClient.DATATYPE.FLOAT32,
            #                                             word_order='little')
            #
            # write_result = client.write_registers(3, values=float_to_regs, device_id=2)  # Записать 123 в регис

            # coils
            coils = client.read_coils(0, count=4, device_id=2)
            if coils.isError():
                print(f"Ошибка чтения: {coils.exception_code}")
            else:
                print(f"Успешно прочитано: {coils.bits}")

        except ModbusException as e:
            # self.logger.error(f"Error in Modbus RTU handler loop: {e}")
            print(f"Произошла ошибка Modbus: {e}")
        except Exception as e:
            # self.logger.error(f"Error in Modbus RTU handler: {e}")
            print(f"Произошла другая ошибка: {e}")
        finally:
            client.close()
            print("Соединение закрыто")

        # if self.heartbeat_cb:
        #     try:
        #         self.heartbeat_cb('modbus RTU')
        #     except Exception:
        #         pass

# if __name__ == "__main__":
# tcp_manager = ModbusTCPManager()
# tcp_manager.run_sync_client()

# rtu_manager = ModbusRTUManager()
# rtu_manager.run_sync_client()
