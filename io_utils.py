"""
Чтение данных из текстовых файлов.
"""

from config import LOGIN_FILE, DATA_FILE


def read_credentials(login_file=LOGIN_FILE):
    """Читает логин и пароль (первая и вторая непустые строки)."""
    with open(login_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f if line.strip()]
    if len(lines) < 2:
        raise Exception(f"В {login_file} нужно минимум 2 непустые строки")
    return lines[0], lines[1]


def read_data_file(data_file=DATA_FILE):
    """
    Читает данные для формы: группа, кому назначен, заявитель.
    Возвращает кортеж из трёх строк (пустые, если строк нет).
    """
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
        return (
            lines[0] if len(lines) > 0 else '',
            lines[1] if len(lines) > 1 else '',
            lines[2] if len(lines) > 2 else '',
        )
    except Exception:
        return '', '', ''