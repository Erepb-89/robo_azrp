import threading
from typing import Dict

from sdnotify import SystemdNotifier


class WatchdogManager(threading.Thread):
    def __init__(self, heartbit, interval_sec=5.0, logger=None):
        super().__init__(daemon=True, name="WatchdogThread")
        self._heartbit = heartbit
        self._interval = interval_sec
        self._logger = logger
        self._stop_event = threading.Event()
        self._notifier = SystemdNotifier()
        self._ready_sent = False

    def set_ready(self):
        """Отправляет сигнал READY в systemd."""
        try:
            self._notifier.notify("READY=1")
            self._ready_sent = True
        except Exception as e:
            self._logger.debug(f"sdnotify READY err: {e}")

    def _get_statuses(self) -> Dict[str, bool]:
        """Получает статусы компонентов."""
        try:
            return self._heartbit.state() or {}
        except Exception as e:
            self._logger.error(f"Failed to get heartbit state: {e}")
            return {}

    @staticmethod
    def _format_status_line(statuses: Dict[str, bool]) -> str:
        """Форматирует строку статуса для systemd."""
        if not statuses:
            return ""

        return "; ".join(
            f"{key}={'ok' if val else 'stale'}"
            for key, val in statuses.items()
        )

    def _process_statuses(self, statuses: Dict[str, bool]) -> None:
        """Обрабатывает статусы, отправляет уведомления."""
        status_line = self._format_status_line(statuses)

        if status_line:
            self._notifier.notify(f"STATUS={status_line}")
            self._logger.info(f"Watchdog status: {status_line}")

        # Отправляем WATCHDOG=1, только если все компоненты в порядке
        if statuses and all(statuses.values()):
            self._notifier.notify("WATCHDOG=1")
            self._logger.debug("WATCHDOG=1 sent (all components OK)")

    def run(self) -> None:
        """Основной цикл watchdog."""
        self._logger.info("Watchdog thread started")

        while not self._stop_event.is_set():
            try:
                statuses = self._get_statuses()
                self._process_statuses(statuses)

            except Exception as e:
                self._logger.error(f"Unexpected error in watchdog loop: {e}")

            # Ожидаем следующий цикл или сигнал остановки
            if self._stop_event.wait(timeout=self._interval):
                break

        self._logger.info("Watchdog thread stopped")

    def stop(self) -> None:
        """Останавливает watchdog и отправляет сигнал STOPPING."""
        self._logger.info("Stopping watchdog...")
        self._stop_event.set()

        try:
            self._notifier.notify("STOPPING=1")
            self._logger.debug("STOPPING=1 sent to systemd")
        except Exception as e:
            self._logger.debug(f"Failed to send STOPPING signal: {e}")
