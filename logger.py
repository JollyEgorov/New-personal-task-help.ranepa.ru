"""
Логгер.

- В консольном режиме (python main.py) — пишет в stdout.
- В --windowed EXE (без консоли) — пишет в ranepa.log рядом с exe,
  потому что sys.stdout = None.

Никаких блокировок между процессами.
"""

import logging
import os
import sys


def _log_file_path() -> str:
    """Файл лога рядом с exe (или рядом со скриптом при запуске из Python)."""
    if getattr(sys, "frozen", False):
        base = os.path.dirname(sys.executable)
    else:
        base = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base, "ranepa.log")


def setup_logger(name="ranepa", level=logging.INFO):
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(level)

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(message)s",
        datefmt="%H:%M:%S",
    )

    # 1) Консоль — только если она есть
    if sys.stdout is not None:
        try:
            sh = logging.StreamHandler(sys.stdout)
            sh.setFormatter(fmt)
            logger.addHandler(sh)
        except Exception:
            pass

    # 2) Файл — всегда (и в консольном, и в windowed-режиме).
    #    В консольном это дублирование удобно: лог остаётся после закрытия окна.
    try:
        fh = logging.FileHandler(_log_file_path(), encoding="utf-8")
        fh.setFormatter(fmt)
        logger.addHandler(fh)
    except Exception:
        # если рядом с exe нет прав на запись — молча продолжаем
        # (хотя бы консоль отработает, если она есть)
        pass

    # 3) Если вообще нет ни одного хендлера — NullHandler,
    #    чтобы logging не сыпал "No handlers could be found"
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())

    return logger