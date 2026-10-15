"""
Заполнение полей формы заявки.
"""

import time
import random
from datetime import datetime

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    TIMEOUT_DEFAULT, TIMEOUT_DROPDOWN, TIMEOUT_SELECT, TIMEOUT_SHORT, POLL_FAST,
)
from web_helpers import find_element_with_fallback, click_via_js
from logger import setup_logger

log = setup_logger()


def _random_time_22_23():
    hour = random.choice([22, 23])
    minute = random.randint(0, 59)
    second = random.randint(0, 59)
    return hour, minute, second


# ========== Дропдауны ==========

def select_from_dropdown(driver, field_container, timeout=TIMEOUT_DROPDOWN):
    """Ждёт появления дропдауна и кликает по первому пункту."""
    xpaths = [
        ".//div[@data-test='suggest-dropdown-item']",
        ".//div[@data-test='custom-select-dropdown-item']",
    ]

    def _first_dropdown(d):
        for xp in xpaths:
            try:
                items = field_container.find_elements(By.XPATH, xp)
                if not items:
                    items = d.find_elements(By.XPATH, xp.replace(".//", "//"))
                if items:
                    return items[0]
            except Exception:
                continue
        return False

    try:
        item = WebDriverWait(driver, timeout, poll_frequency=POLL_FAST).until(_first_dropdown)
    except Exception:
        return False

    try:
        item.click()
        return True
    except Exception:
        return click_via_js(driver, item)

def _close_any_dropdown(driver):
    """Пытается закрыть любой открытый дропдаун/оверлей."""
    try:
        from selenium.webdriver.common.action_chains import ActionChains
        ActionChains(driver).send_keys(Keys.ESCAPE).perform()
    except Exception:
        pass
    time.sleep(0.15)

def _select_custom_option(driver, field_test_id, target_text):
    """Общая логика для custom-select (Статус, Срочность).
    Устойчива к element click intercepted."""
    from selenium.webdriver.common.action_chains import ActionChains

    # Сначала закрываем возможные оверлеи от предыдущих полей
    _close_any_dropdown(driver)

    try:
        field = WebDriverWait(driver, TIMEOUT_SELECT, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//div[@data-test='{field_test_id}']")
            )
        )
        button = WebDriverWait(field, TIMEOUT_DEFAULT, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH, ".//button[@data-test='custom-select-button']")
            )
        )

        # Скроллим и кликаем через JS — обходит перехват оверлеем
        driver.execute_script(
            "arguments[0].scrollIntoView({block: 'center'});", button
        )
        time.sleep(0.1)

        try:
            button.click()
        except Exception:
            # fallback: JS-клик, если обычный перехвачен
            driver.execute_script("arguments[0].click();", button)

        # Ждём именно элемент списка, кликаем тоже через fallback
        item = WebDriverWait(driver, TIMEOUT_SELECT, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 f"//div[@data-test='custom-select-dropdown-item' "
                 f"and normalize-space(text())='{target_text}']")
            )
        )
        try:
            item.click()
        except Exception:
            driver.execute_script("arguments[0].click();", item)

        _close_any_dropdown(driver)
        return True
    except Exception as e:
        log.error(f"    ✗ Ошибка выбора '{target_text}': {str(e)[:160]}")
        _close_any_dropdown(driver)
        return False


# ========== Rich-text ==========

def fill_rich_text_field(driver, field_test_id_or_xpath, search_text, description=""):
    """Заполняет rich-text (WYSIWYG) поле (Lexical)."""
    log.info(f"  → {description}: ввожу '{search_text}'")
    try:
        if field_test_id_or_xpath.startswith("//"):
            wrapper = WebDriverWait(driver, TIMEOUT_DEFAULT, poll_frequency=POLL_FAST).until(
                EC.presence_of_element_located((By.XPATH, field_test_id_or_xpath))
            )
        else:
            wrapper = find_element_with_fallback(driver, [
                ("xpath", f"//div[@data-test='{field_test_id_or_xpath}']"),
                ("xpath",
                 "//div[@data-test-field-type='wysiwyg' "
                 "and .//span[contains(text(), 'Описание')]]"),
            ], timeout=TIMEOUT_DEFAULT)

        if not wrapper:
            log.error(f"  ✗ {description}: обёртка поля не найдена")
            return False

        editable = find_element_with_fallback(wrapper, [
            ("xpath", ".//div[@data-lexical-editor='true']"),
            ("xpath", ".//div[@contenteditable='true']"),
            ("xpath", ".//div[@role='textbox']"),
        ], timeout=TIMEOUT_DEFAULT)

        if not editable:
            log.error(f"  ✗ {description}: contenteditable не найден")
            return False

        driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", editable)
        try:
            editable.click()
        except Exception:
            click_via_js(driver, editable)

        editable.send_keys(Keys.CONTROL, "a")
        editable.send_keys(Keys.DELETE)
        editable.send_keys(search_text)
        editable.send_keys(Keys.TAB)

        log.info(f"  ✓ {description} - заполнено")
        return True
    except Exception as e:
        log.error(f"  ✗ {description}: {str(e)[:120]}")
        return False


# ========== Reference-поля ==========

def fill_reference_field(driver, field_test_id, data_line, description=""):
    """Заполняет reference-поле: очистка → ввод → выбор первого пункта."""
    if not data_line:
        log.warning(f"  ⚠ {description}: нет данных")
        return False

    log.info(f"  → {description}: меняю на '{data_line}'")

    try:
        field_container = WebDriverWait(driver, TIMEOUT_DEFAULT, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH, f"//div[@data-test='{field_test_id}']")
            )
        )

        clear_button = find_element_with_fallback(field_container, [
            ("xpath", ".//button[contains(@class, 'FieldClear___')]"),
            ("xpath", ".//button[@data-test='clear-field-button']"),
            ("xpath", ".//button[contains(@class, 'clear-button')]"),
        ], timeout=TIMEOUT_SHORT)

        if clear_button:
            try:
                clear_button.click()
                log.info("    → Очищаю поле")
            except Exception:
                click_via_js(driver, clear_button)

        input_field = None
        for by, sel in [
            (By.XPATH, ".//input[@type='text']"),
            (By.XPATH, ".//input[@type='search']"),
            (By.XPATH, ".//input"),
        ]:
            try:
                input_field = WebDriverWait(field_container, 3, poll_frequency=POLL_FAST).until(
                    EC.element_to_be_clickable((by, sel))
                )
                break
            except Exception:
                continue

        if not input_field:
            try:
                input_field = WebDriverWait(field_container, 2, poll_frequency=POLL_FAST).until(
                    EC.element_to_be_clickable(
                        (By.XPATH, ".//div[@contenteditable='true']")
                    )
                )
            except Exception:
                field_container.click()
                input_field = driver.switch_to.active_element

        try:
            input_field.click()
        except Exception:
            click_via_js(driver, input_field)

        input_field.send_keys(Keys.CONTROL, "a")
        input_field.send_keys(Keys.DELETE)
        input_field.send_keys(data_line)

        if not select_from_dropdown(driver, field_container):
            log.warning("    ✗ Дропдаун не появился")
            _close_any_dropdown(driver)
            return False

        # Закрываем дропдаун: ESC через ActionChains + клик по нейтральному месту
        _close_any_dropdown(driver)

        log.info(f"  ✓ {description} - изменено")
        return True
    except Exception as e:
        log.error(f"  ✗ {description}: {str(e)[:120]}")
        return False


def update_status(driver, target_text):
    log.info(f"  → Статус: '{target_text}'")
    if _select_custom_option(driver, "state-field-select", target_text):
        log.info(f"  ✓ Статус: '{target_text}'")
        return True
    log.error("  ✗ Статус: не удалось")
    return False


def update_urgency(driver, target_text):
    log.info(f"  → Срочность: '{target_text}'")
    if _select_custom_option(driver, "urgency-field-select", target_text):
        log.info(f"  ✓ Срочность: '{target_text}'")
        return True
    log.error("  ✗ Срочность: не удалось")
    return False


# ========== Дата/время ==========

def fill_datetime_field(driver, value_str=None, random_evening=False):
    """Заполняет поле даты/времени. Формат 'DD.MM.YYYY HH:MM:SS'."""
    if value_str is None:
        today = datetime.now().strftime("%d.%m.%Y")
        if random_evening:
            h, m, s = _random_time_22_23()
            value_str = f"{today} {h:02d}:{m:02d}:{s:02d}"
        else:
            value_str = datetime.now().strftime("%d.%m.%Y %H:%M:%S")

    log.info(f"  → Дата/время: '{value_str}'")
    digits = ''.join(ch for ch in value_str if ch.isdigit())

    # Стратегия 1: клик по маске + send_keys
    try:
        mask = WebDriverWait(driver, TIMEOUT_DEFAULT, poll_frequency=POLL_FAST).until(
            EC.element_to_be_clickable(
                (By.XPATH, "//span[contains(@class, 'TabMask')]")
            )
        )
        mask.click()
        active = driver.switch_to.active_element
        active.send_keys(digits)
        active.send_keys(Keys.TAB)
        log.info(f"  ✓ Дата/время: '{value_str}'")
        return True
    except Exception as e:
        log.warning(f"    → Стратегия 1 не сработала: {str(e)[:80]}")

    # Стратегия 2: JS
    try:
        hidden_input = WebDriverWait(driver, TIMEOUT_SELECT, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH,
                 "//input[@type='number' and contains(@class, 'HiddenInput')]")
            )
        )
        driver.execute_script("""
            const el = arguments[0];
            const value = arguments[1];
            const nativeInputValueSetter = Object.getOwnPropertyDescriptor(
                window.HTMLInputElement.prototype, 'value'
            ).set;
            nativeInputValueSetter.call(el, value);
            el.dispatchEvent(new Event('input', { bubbles: true }));
            el.dispatchEvent(new Event('change', { bubbles: true }));
        """, hidden_input, digits)
        driver.execute_script("arguments[0].blur();", hidden_input)
        log.info(f"  ✓ Дата/время (JS): '{value_str}'")
        return True
    except Exception as e:
        log.error(f"  ✗ Дата/время: {str(e)[:120]}")
        return False


# ========== Текстовые поля ==========

def fill_text_field(driver, field_test_ids, search_text, description=""):
    """Заполнение текстовых полей (например, Тема)."""
    log.info(f"  → {description}: ввожу '{search_text}'")

    if isinstance(field_test_ids, str):
        field_test_ids = [field_test_ids]

    field_container = None
    for test_id in field_test_ids:
        field_container = find_element_with_fallback(driver, [
            ("xpath", f"//div[@data-test='{test_id}']"),
            ("xpath", f"//textarea[@data-test='{test_id}']"),
        ], timeout=2)
        if field_container:
            log.info(f"    → Найдено по data-test='{test_id}'")
            break

    if not field_container:
        log.error(f"  ✗ {description}: поле не найдено")
        return False

    try:
        textarea_field = find_element_with_fallback(field_container, [
            ("xpath", ".//textarea"),
        ], timeout=2)

        if textarea_field:
            try:
                textarea_field.click()
            except Exception:
                click_via_js(driver, textarea_field)
            textarea_field.clear()
            textarea_field.send_keys(search_text)
        else:
            input_field = find_element_with_fallback(field_container, [
                ("xpath", ".//input[@type='text']"),
                ("xpath", ".//input[@type='search']"),
                ("xpath", ".//input"),
            ], timeout=2)

            if input_field:
                try:
                    input_field.click()
                except Exception:
                    click_via_js(driver, input_field)
                input_field.clear()
                input_field.send_keys(search_text)
            else:
                field_container.click()
                driver.switch_to.active_element.send_keys(search_text)

        log.info(f"  ✓ {description} - заполнено")
        return True
    except Exception as e:
        log.error(f"  ✗ {description}: {str(e)[:100]}")
        return False

# ========== Проверка заполненности (read-only) ==========

def _container_has_value(field_container) -> bool:
    """
    Универсальный признак «в поле что-то выбрано/введено».
    Работает для reference-полей, custom-select и текстовых.
    """
    try:
        # 1) input/textarea с непустым value
        for inp in field_container.find_elements(By.XPATH, ".//input | .//textarea"):
            val = (inp.get_attribute("value") or "").strip()
            if val:
                return True

        # 2) чипы/теги/выбранные значения
        for c in field_container.find_elements(
            By.XPATH,
            ".//*[contains(@class, 'Chip') or contains(@class, 'Tag') "
            "or contains(@class, 'Value') or contains(@class, 'selected') "
            "or contains(@class, 'SingleValue')]"
        ):
            if (c.text or "").strip():
                return True

        # 3) contenteditable с текстом
        for ce in field_container.find_elements(
            By.XPATH, ".//div[@contenteditable='true']"
        ):
            if (ce.text or "").strip():
                return True

        return False
    except Exception:
        return False


def check_reference_filled(driver, field_test_id) -> bool:
    """Проверяет, что reference-поле содержит значение."""
    try:
        container = driver.find_element(
            By.XPATH, f"//div[@data-test='{field_test_id}']"
        )
        return _container_has_value(container)
    except Exception:
        return False


def check_custom_select_filled(driver, field_test_id, expected_text=None) -> bool:
    """Проверяет custom-select (Статус, Срочность)."""
    try:
        field = driver.find_element(
            By.XPATH, f"//div[@data-test='{field_test_id}']"
        )
        button = field.find_element(
            By.XPATH, ".//button[@data-test='custom-select-button']"
        )
        text = (button.text or "").strip()
        if not text:
            return False
        if expected_text:
            return expected_text.strip() in text
        return True
    except Exception:
        return False


def check_text_filled(driver, field_test_ids, expected_text=None) -> bool:
    """Проверяет текстовое поле (Тема)."""
    if isinstance(field_test_ids, str):
        field_test_ids = [field_test_ids]

    for test_id in field_test_ids:
        for xp in (
            f"//div[@data-test='{test_id}']",
            f"//textarea[@data-test='{test_id}']",
        ):
            try:
                container = driver.find_element(By.XPATH, xp)
            except Exception:
                continue

            for inp in container.find_elements(By.XPATH, ".//input | .//textarea"):
                val = (inp.get_attribute("value") or "").strip()
                if val and (expected_text is None or expected_text.strip() in val):
                    return True

            txt = (container.text or "").strip()
            if txt and (expected_text is None or expected_text.strip() in txt):
                return True
    return False


def check_rich_text_filled(driver, field_test_id, expected_text=None) -> bool:
    """Проверяет rich-text (Описание)."""
    try:
        wrapper = driver.find_element(
            By.XPATH, f"//div[@data-test='{field_test_id}']"
        )
    except Exception:
        return False

    for ce in wrapper.find_elements(
        By.XPATH, ".//div[@data-lexical-editor='true'] | .//div[@contenteditable='true']"
    ):
        txt = (ce.text or "").strip()
        if txt and (expected_text is None or expected_text.strip() in txt):
            return True
    return False


def check_datetime_filled(driver) -> bool:
    """
    Проверяет поле даты/времени.
    Признак: в маске есть цифры даты, либо в hidden-input есть значение.
    """
    # По маске
    try:
        masks = driver.find_elements(
            By.XPATH, "//span[contains(@class, 'TabMask')]"
        )
        for m in masks:
            txt = (m.text or "").strip()
            if txt and any(ch.isdigit() for ch in txt):
                # dd.mm.yyyy — минимум 8 цифр
                if sum(ch.isdigit() for ch in txt) >= 8:
                    return True
    except Exception:
        pass

    # По hidden input
    try:
        for inp in driver.find_elements(
            By.XPATH,
            "//input[@type='number' and contains(@class, 'HiddenInput')]",
        ):
            if (inp.get_attribute("value") or "").strip():
                return True
    except Exception:
        pass

    return False