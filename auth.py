"""
Авторизация на портале РАНХиГС.

Cookies не используются. Каждый запуск — чистая сессия.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import (
    TIMEOUT_LOGIN_FIELD, TIMEOUT_SHORT, TIMEOUT_FORM_AFTER_LOGIN,
    LOGIN_BUTTON_TEXTS, POLL_FAST,
)
from web_helpers import find_element_with_fallback, click_via_js
from logger import setup_logger

log = setup_logger()


# ============================================================
# Ожидания
# ============================================================

def wait_for_username_field(driver, timeout=TIMEOUT_LOGIN_FIELD):
    """Ожидание появления поля ввода логина."""
    log.info("  → Ожидаю поле логина...")
    field = find_element_with_fallback(driver, [
        ("xpath", "//input[@data-test='username-login-field']"),
    ], timeout=timeout)
    if field and field.is_displayed() and field.is_enabled():
        log.info("  ✓ Поле логина появилось")
        return field
    log.warning("  ✗ Поле логина не появилось")
    return None


def is_form_ready(driver, timeout=TIMEOUT_FORM_AFTER_LOGIN):
    """Признак авторизации — появилось поле 'Заявитель'."""
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH, "//*[@data-test='caller-field-reference']")
            )
        )
        return True
    except Exception:
        return False


def is_login_page(driver, timeout=2):
    """Признак того, что мы на странице логина."""
    try:
        WebDriverWait(driver, timeout, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located(
                (By.XPATH, "//input[@data-test='username-login-field']")
            )
        )
        return True
    except Exception:
        return False


# ============================================================
# Логин
# ============================================================

def login(driver, username, password):
    """Выполняет авторизацию. Возвращает True, если форма появилась."""
    log.info("\n[1] Авторизация...")
    try:
        username_field = find_element_with_fallback(driver, [
            ("xpath", "//input[@data-test='username-login-field']"),
            ("xpath", "//input[@placeholder='Логин' or @placeholder='Email' or @type='email']"),
        ], timeout=5)

        password_field = find_element_with_fallback(driver, [
            ("xpath", "//input[@type='password' or @placeholder='Пароль']"),
        ], timeout=5)

        if not username_field or not password_field:
            log.warning("  ⚠ Полей входа нет — возможно, уже авторизованы")
            return is_form_ready(driver, timeout=TIMEOUT_SHORT)

        log.info(f"  → Логин: {username}")
        username_field.clear()
        username_field.send_keys(username)

        log.info("  → Пароль")
        password_field.clear()
        password_field.send_keys(password)

        login_button = None
        for text in LOGIN_BUTTON_TEXTS:
            login_button = find_element_with_fallback(driver, [
                ("xpath",
                 f"//button[contains(text(), '{text}')] "
                 f"| //input[@type='submit' and contains(@value, '{text}')]"),
            ], timeout=TIMEOUT_SHORT)
            if login_button:
                break

        if login_button:
            log.info("  → Кнопка входа")
            try:
                login_button.click()
            except Exception:
                click_via_js(driver, login_button)
        else:
            log.info("  → Enter в поле пароля")
            password_field.send_keys(Keys.ENTER)

        if not is_form_ready(driver, timeout=TIMEOUT_FORM_AFTER_LOGIN):
            log.error("  ✗ Форма не появилась после логина")
            return False
        return True
    except Exception as e:
        log.error(f"  ⚠ Ошибка авторизации: {e}")
        return False


# ============================================================
# Высокоуровневая функция
# ============================================================

def ensure_logged_in(driver, username, password, base_url):
    """
    Открывает URL и гарантирует, что мы на форме.
    Никаких cookies: если форма не готова — сразу логин.
    """
    driver.get(base_url)

    # Быстрая проверка: форма или логин?
    try:
        WebDriverWait(driver, 3, poll_frequency=POLL_FAST).until(
            lambda d: (
                d.find_elements(By.XPATH, "//*[@data-test='caller-field-reference']")
                or d.find_elements(By.XPATH, "//input[@data-test='username-login-field']")
            )
        )
    except Exception:
        pass

    if is_form_ready(driver, timeout=1):
        log.info("✓ Форма уже доступна")
        return True

    if login(driver, username, password):
        return True
    return False