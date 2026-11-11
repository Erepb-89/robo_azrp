import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from queue import Full
import os
import tempfile
from typing import Any


class GuiLogFilter(logging.Filter):
    """Пропускает в GUI ошибки/предупреждения и события robopro.gui.*."""

    def filter(self, record: logging.LogRecord) -> bool:
        return (record.levelno >= logging.WARNING
                or record.name.startswith("robopro.gui"))


class GuiLogHandler(logging.Handler):
    """Неблокирующий мост logging -> очередь GUI-журнала."""

    def __init__(self, gui_queue):
        super().__init__()
        self.gui_queue = gui_queue
        self.dropped = 0

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self.gui_queue.put_nowait(
                (record.levelno, record.name, record.getMessage()))
        except Full:
            self.dropped += 1
        except Exception:
            self.handleError(record)


def setup_logging(log_path: Path, gui_queue=None) -> logging.Logger:
    logger = logging.getLogger("robopro")
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        handler = RotatingFileHandler(log_path, maxBytes=2_000_000,
                                      backupCount=3, encoding="utf-8")
        fmt = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(threadName)s %(name)s: %(message)s")
        handler.setFormatter(fmt)
        logger.addHandler(handler)
        # плюс вывод в консоль
        console = logging.StreamHandler()
        console.setFormatter(fmt)
        logger.addHandler(console)
    if gui_queue is not None and not any(
            isinstance(handler, GuiLogHandler) for handler in logger.handlers):
        gui_handler = GuiLogHandler(gui_queue)
        gui_handler.setLevel(logging.INFO)
        gui_handler.addFilter(GuiLogFilter())
        gui_handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(gui_handler)
    return logger


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", delete=False, dir=str(path.parent),
                                     encoding="utf-8") as tmp:
        json.dump(data, tmp, indent=4, ensure_ascii=False)
        tmp.flush()
        os.fsync(tmp.fileno())
        tmp_path = Path(tmp.name)
    os.replace(tmp_path, path)


def read_json(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
