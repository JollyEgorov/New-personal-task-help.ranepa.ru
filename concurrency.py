"""
Ограничение параллелизма: не более MAX_PARALLEL процессов одновременно.
Реализовано через файловые локи в TEMP. Не мешает соседям.
"""

import os
import time

from config import MAX_PARALLEL, LOCK_TIMEOUT

LOCK_DIR = os.path.join(os.environ.get('TEMP', '.'), 'ranepa_locks')


def _cleanup_dead_locks():
    """Удаляет локи умерших процессов."""
    try:
        for f in os.listdir(LOCK_DIR):
            path = os.path.join(LOCK_DIR, f)
            try:
                pid = int(f)
                # os.kill(pid, 0) не отправляет сигнал, только проверяет процесс
                os.kill(pid, 0)
            except Exception:
                try:
                    os.remove(path)
                except Exception:
                    pass
    except FileNotFoundError:
        pass


def acquire_slot(timeout=LOCK_TIMEOUT, poll=0.3):
    """Ждёт свободный слот. Возвращает путь к лок-файлу."""
    os.makedirs(LOCK_DIR, exist_ok=True)
    end = time.time() + timeout
    lock_path = os.path.join(LOCK_DIR, str(os.getpid()))

    while time.time() < end:
        _cleanup_dead_locks()

        if len(os.listdir(LOCK_DIR)) < MAX_PARALLEL:
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                return lock_path
            except FileExistsError:
                pass

        time.sleep(poll)

    raise TimeoutError(f"Не дождались слота параллелизма за {timeout} сек")


def release_slot(lock_path):
    try:
        os.remove(lock_path)
    except Exception:
        pass