"""
Точка входа.

Сценарий:
  1. Ограничение параллелизма (файловый лок).
  2. Запуск Chrome с временным профилем.
  3. Авторизация (без cookies).
  4. Полное заполнение формы.
  5. Сбор полей, вернувших ошибку → повторный проход только по ним.
  6. Итоговый отчёт.
  7. Ожидание закрытия окна пользователем.
"""

import sys
import time

from logger import setup_logger
from runtime import LOGIN_FILE, DATA_FILE
from io_utils import read_credentials, read_data_file
from concurrency import acquire_slot, release_slot
from browser import create_driver

from config import (
    FORM_URL,
    TOTAL_FIELDS,
    FIELD_CALLER, FIELD_ASSIGNMENT_GROUP, FIELD_ASSIGNED_USER,
    FIELD_STATUS, FIELD_URGENCY,
    FIELD_SUBJECT_IDS, FIELD_DESCRIPTION_RICH,
    STATUS_VALUE, URGENCY_VALUE, SUBJECT_TEXT, DESCRIPTION_TEXT,
    FIELD_RETRY_ATTEMPTS, FIELD_RETRY_DELAY,
)
from auth import ensure_logged_in
from form_fields import (
    fill_reference_field, fill_text_field, fill_rich_text_field,
    update_status, update_urgency, fill_datetime_field,
)

log = setup_logger()

def _finalize(driver, lock_path, exit_code=0):
    """
    Жёсткое завершение:
      1. Снимаем лок.
      2. Флашим логи.
      3. Прибиваем chromedriver.exe (Chrome остаётся).
      4. os._exit — finally НЕ выполняется, quit() НЕ зовётся.
    """
    import os
    import logging as _logging
    import subprocess

    # 1. Лок
    if lock_path:
        try:
            release_slot(lock_path)
        except Exception:
            pass

    # 2. Логи
    for h in _logging.getLogger("ranepa").handlers:
        try:
            h.flush()
        except Exception:
            pass
    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass

    # 3. Прибиваем chromedriver.exe. Chrome не тронет — он уже detached.
    if driver is not None:
        try:
            cd_pid = driver.service.process.pid
            subprocess.run(
                ["taskkill", "/F", "/PID", str(cd_pid)],
                capture_output=True,
                timeout=5,
            )
        except Exception:
            pass

    # 4. Мгновенный выход
    os._exit(exit_code)

# ============================================================
# Реестр полей: имя → функция-заполнитель
# ============================================================

def build_registry(driver, group, assigned, caller):
    """
    Каждая функция возвращает True при успехе и False при неудаче.
    Именно по этому признаку поле попадает (или нет) в список на повтор.
    """
    return {
        "Заявитель": lambda: fill_reference_field(
            driver, FIELD_CALLER, caller, "Заявитель"),
        "Группа": lambda: fill_reference_field(
            driver, FIELD_ASSIGNMENT_GROUP, group, "Группа"),
        "Кому назначено": lambda: fill_reference_field(
            driver, FIELD_ASSIGNED_USER, assigned, "Кому назначено"),
        "Тема": lambda: fill_text_field(
            driver, FIELD_SUBJECT_IDS, SUBJECT_TEXT, "Тема"),
        "Описание": lambda: fill_rich_text_field(
            driver, FIELD_DESCRIPTION_RICH, DESCRIPTION_TEXT, "Описание"),
        "Статус": lambda: update_status(driver, STATUS_VALUE),
        "Срочность": lambda: update_urgency(driver, URGENCY_VALUE),
        "Дата/время": lambda: fill_datetime_field(driver, random_evening=True),
    }


# ============================================================
# Заполнение с ретраями по неудавшимся
# ============================================================

def _run_pass(registry, names, pass_label):
    """
    Прогоняет writer-функции по указанным именам.
    Возвращает список имён, которые вернули False/исключение.
    """
    failed = []
    for name in names:
        writer = registry[name]
        try:
            ok = bool(writer())
        except Exception as e:
            log.error(f"  ✗ {name}: исключение {str(e)[:120]}")
            ok = False

        if ok:
            log.info(f"  ✓ {name}")
        else:
            log.warning(f"  ✗ {name}: не заполнено")
            failed.append(name)
    return failed


def fill_all_with_verification(driver, group, assigned, caller):
    """
    1) Полный проход по всем полям.
    2) Собираем те, что вернули False.
    3) Повторные проходы только по ним.
    """
    log.info("\n[2] Заполнение полей формы...")
    registry = build_registry(driver, group, assigned, caller)
    all_names = list(registry.keys())

    # --- Проход 1: все поля ---
    failed = _run_pass(registry, all_names, "проход 1")

    filled_count = len(all_names) - len(failed)
    log.info(f"\n  Итог прохода 1: {filled_count}/{len(all_names)} заполнено")
    if failed:
        log.warning(f"  Не заполнено: {failed}")

    # --- Повторные проходы только по неудавшимся ---
    for attempt in range(1, FIELD_RETRY_ATTEMPTS):
        if not failed:
            break

        log.info(f"\n[2.{attempt}] Повтор по {len(failed)} полям: {failed}")
        time.sleep(FIELD_RETRY_DELAY)

        still_failed = _run_pass(registry, list(failed), f"проход {attempt + 1}")
        filled_count = len(all_names) - len(still_failed)

        log.info(f"  Итог прохода {attempt + 1}: "
                 f"{filled_count}/{len(all_names)} заполнено")
        if still_failed:
            log.warning(f"  Всё ещё не заполнено: {still_failed}")

        failed = still_failed

    # --- Итог ---
    if failed:
        log.error(f"\n✗ Итог: не заполнено — {failed}")
    else:
        log.info("\n✓ Итог: все поля заполнены")

    return not failed


# ============================================================
# Точка входа
# ============================================================

def main():
    lock_path = None
    driver = None
    try:
        # 1. Ограничение параллелизма
        log.info("Ожидание слота параллелизма...")
        lock_path = acquire_slot()
        log.info("✓ Слот получен")

        # 2. Чтение данных
        username, password = read_credentials(LOGIN_FILE)
        group, assigned, caller = read_data_file(DATA_FILE)

        # 3. Браузер
        log.info("\n[0] Запуск браузера...")
        driver = create_driver(headless=False)
        log.info("✓ Браузер запущен")

        # 4. Авторизация
        if not ensure_logged_in(driver, username, password, FORM_URL):
            log.error("✗ Не удалось авторизоваться или открыть форму")
            return 1

        # 5. Заполнение с ретраями
        ok = fill_all_with_verification(driver, group, assigned, caller)

        if ok:
            log.info(f"\n✓ Форма заполнена ({TOTAL_FIELDS} полей)")
        else:
            log.error("\n✗ Форма заполнена не полностью — проверьте вручную")

        # 6. Готово — выходим, браузер оставляем открытым
                # 6. Готово — жёсткий выход, Chrome оставляем открытым
        log.info("\n✓ Заполнение завершено. Браузер оставлен открытым.")

        _finalize(driver, lock_path, exit_code=(0 if ok else 2))
        # _finalize не возвращает управление — вызывает os._exit

    except TimeoutError as e:
        log.error(f"✗ {e}")
        return 3
    except Exception as e:
        log.error(f"✗ Критическая ошибка: {e}")
        return 1
    finally:
        if lock_path:
            release_slot(lock_path)
        # driver НЕ закрываем — Chrome должен остаться открытым


if __name__ == "__main__":
    sys.exit(main())