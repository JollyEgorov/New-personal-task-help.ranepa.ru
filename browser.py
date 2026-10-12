"""
Запуск браузера и ожидание его закрытия.

Профиль не используется — Chrome стартует с временным,
который удаляется при driver.quit().
"""

import os
import sys
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService

from logger import setup_logger

log = setup_logger()


def create_driver(headless=False):
    """Создаёт Chrome WebDriver с временным профилем (по умолчанию у Chrome)."""
    options = webdriver.ChromeOptions()

    options.add_argument("--no-first-run")
    options.add_argument("--no-default-browser-check")
    options.add_argument("--disable-extensions")
    options.add_argument("--disable-popup-blocking")
    options.add_argument("--disable-background-networking")
    options.add_argument("--disable-sync")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-features=Translate,BackForwardCache,ServiceWorker")
    options.add_argument("--disable-gpu")
    options.add_argument("--log-level=3")

    if headless:
        options.add_argument("--headless=new")

    driver = webdriver.Chrome(
        options=options,
        service=ChromeService(),
    )
    driver.set_page_load_timeout(30)
    return driver


def wait_for_browser_close(driver, poll_interval=0.3):
    """Блокирует выполнение, пока пользователь не закроет окно браузера."""
    try:
        while True:
            try:
                _ = driver.current_url
            except Exception:
                log.info("\n\nБраузер закрыт. Завершение работы...")
                break
            if not driver.window_handles:
                log.info("\n\nОкно браузера закрыто. Завершение работы...")
                break
            time.sleep(poll_interval)
    except KeyboardInterrupt:
        log.info("\n\nЗавершение по Ctrl+C...")


def _hard_exit(driver=None):
    """Корректно завершает драйвер и процесс без висящих потоков."""
    if driver is not None:
        try:
            driver.quit()
        except Exception:
            pass

    try:
        sys.stdout.flush()
        sys.stderr.flush()
    except Exception:
        pass

    os._exit(0)