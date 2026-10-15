"""
Универсальные помощники для Selenium:
поиск с fallback, ожидания, клики.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from config import POLL_FAST


def _resolve(selector_type, selector_value):
    if selector_type == "xpath":
        return By.XPATH, selector_value
    if selector_type == "tag":
        return By.TAG_NAME, selector_value
    if selector_type == "by":
        return selector_value  # уже (By.X, "...")
    return None, None


def find_element_with_fallback(driver, selectors, timeout=5, description=""):
    """
    Возвращает первый найденный элемент из списка селекторов.
    Быстрый polling — 30 мс.
    """
    end = timeout

    def _probe(d):
        for st, sv in selectors:
            by, val = _resolve(st, sv)
            if by is None:
                continue
            try:
                el = d.find_element(by, val)
                if el:
                    return el
            except Exception:
                continue
        return False

    try:
        return WebDriverWait(driver, end, poll_frequency=POLL_FAST).until(_probe)
    except Exception:
        return None


def find_elements_with_fallback(driver, selectors, description=""):
    """Возвращает первый непустой список из нескольких селекторов."""
    for st, sv in selectors:
        by, val = _resolve(st, sv)
        if by is None:
            continue
        try:
            elements = driver.find_elements(by, val)
            if elements:
                return elements
        except Exception:
            continue
    return []


def wait_for_visible(driver, by, value, timeout=5):
    try:
        return WebDriverWait(driver, timeout, poll_frequency=POLL_FAST).until(
            EC.visibility_of_element_located((by, value))
        )
    except Exception:
        return None


def wait_for_presence(driver, by, value, timeout=5, description=""):
    try:
        return WebDriverWait(driver, timeout, poll_frequency=POLL_FAST).until(
            EC.presence_of_element_located((by, value))
        )
    except Exception:
        return None


def wait_and_click(driver, by, value, timeout=5):
    try:
        el = WebDriverWait(driver, timeout, poll_frequency=POLL_FAST).until(
            EC.element_to_be_clickable((by, value))
        )
        el.click()
        return True
    except Exception:
        return False


def click_element_safely(driver, element, fallback_selector=None, description=""):
    try:
        element.click()
        return True
    except Exception:
        if fallback_selector:
            try:
                if isinstance(fallback_selector, tuple):
                    fallback_elem = driver.find_element(*fallback_selector)
                else:
                    fallback_elem = driver.find_element(By.XPATH, fallback_selector)
                fallback_elem.click()
                return True
            except Exception:
                pass
        return False


def click_via_js(driver, element):
    try:
        driver.execute_script("arguments[0].click();", element)
        return True
    except Exception:
        return False

def safe_get_text(element):
    """Безопасно достаёт текст/значение элемента."""
    try:
        tag = (element.tag_name or "").lower()
        if tag in ("input", "textarea"):
            return (element.get_attribute("value") or "").strip()
        return (element.text or "").strip()
    except Exception:
        return ""


def element_exists(driver, xpath, timeout=0.5):
    """Быстрая проверка наличия элемента без ожидания."""
    try:
        els = driver.find_elements(By.XPATH, xpath)
        return els[0] if els else None
    except Exception:
        return None