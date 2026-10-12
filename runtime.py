"""
Пути к файлам рядом с exe. Никаких cookies, никаких профилей.
Всё изменяемое — во временной папке ОС, которую Chrome чистит сам.
"""

import os
import sys


def _base_dir() -> str:
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


BASE_DIR = _base_dir()

# Пользовательские файлы — читаются, лежат рядом с exe
LOGIN_FILE = os.path.join(BASE_DIR, 'login.txt')
DATA_FILE = os.path.join(BASE_DIR, 'data.txt')