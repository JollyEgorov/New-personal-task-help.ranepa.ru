"""
Точка входа: авторизация + заполнение формы заявки РАНХиГС.
"""

import os
import sys

from config import (
    FORM_URL,
    FIELD_CALLER, FIELD_ASSIGNMENT_GROUP, FIELD_ASSIGNED_USER,
    FIELD_SUBJECT_IDS,
    STATUS_VALUE, URGENCY_VALUE,
    SUBJECT_TEXT, DESCRIPTION_TEXT,
    TOTAL_FIELDS,
    FIELD_DESCRIPTION_RICH,
)
from io_utils import read_credentials, read_data_file
from browser import create_driver, wait_for_browser_close, _hard_exit
from auth import ensure_logged_in
from form_fields import (
    fill_rich_text_field,
    fill_reference_field,
    update_status,
    update_urgency,
    fill_datetime_field,
    fill_text_field,
)
from logger import setup_logger
from concurrency import acquire_slot, release_slot

log = setup_logger()


def print_final_result(successful, total, group, assigned, caller):
    log.info("\n" + "=" * 60)
    log.info(f"✅ ЗАПОЛНЕНО {successful}/{total} ПОЛЕЙ")
    log.info("=" * 60)
    log.info("\nСтраница открыта для проверки.")
    log.info("Окно браузера останется открытым.")
    log.info("Закройте браузер чтобы завершить работу скрипта.")


def main():
    log.info("=" * 60)
    log.info("АВТОМАТИЗАЦИЯ РАНХиГС")
    log.info("=" * 60)

    username, password = read_credentials()
    group_data, assigned_data, caller_data = read_data_file()
    log.info("✓ Данные загружены:")
    log.info(f"  Группа: '{group_data}'")
    log.info(f"  Назначен: '{assigned_data}'")
    log.info(f"  Заявитель: '{caller_data}'")

    driver = None
    lock_path = None

    try:
        lock_path = acquire_slot()
        driver = create_driver()

        log.info("\n[1] Проверяю авторизацию...")
        if not ensure_logged_in(driver, username, password, FORM_URL):
            log.error("Не удалось авторизоваться. Завершение.")
            _hard_exit(driver)

        log.info("\n[2] Заполняю поля:")
        successful = 0

        if fill_reference_field(driver, FIELD_CALLER, caller_data, "Заявитель"):
            successful += 1
        if fill_reference_field(driver, FIELD_ASSIGNMENT_GROUP, group_data,
                                "Назначено на группу"):
            successful += 1
        if fill_reference_field(driver, FIELD_ASSIGNED_USER, assigned_data,
                                "Кому назначен"):
            successful += 1
        if update_status(driver, STATUS_VALUE):
            successful += 1
        if update_urgency(driver, URGENCY_VALUE):
            successful += 1
        if fill_datetime_field(driver, random_evening=True):
            successful += 1
        if fill_text_field(driver, FIELD_SUBJECT_IDS, SUBJECT_TEXT, "Тема"):
            successful += 1
        if fill_rich_text_field(driver, FIELD_DESCRIPTION_RICH,
                                DESCRIPTION_TEXT, "Описание"):
            successful += 1

        print_final_result(successful, TOTAL_FIELDS,
                           group_data, assigned_data, caller_data)

        wait_for_browser_close(driver)

    except Exception as e:
        log.error(f"\nОшибка в основном блоке: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if lock_path:
            release_slot(lock_path)
        _hard_exit(driver)


if __name__ == "__main__":
    main()