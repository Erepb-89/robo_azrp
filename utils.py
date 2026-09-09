import json
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import os
import tempfile
from typing import Any


def setup_logging(log_path: Path) -> logging.Logger:
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
