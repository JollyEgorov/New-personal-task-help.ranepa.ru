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
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--disable-accelerated-2d-canvas")
    options.add_argument("--log-level=3")

    # Ключевой флаг: Chrome не закрывается при завершении chromedriver
    options.add_argument("--detach")

    if headless:
        options.add_argument("--headless=new")

    service = ChromeService()
    
    driver = webdriver.Chrome(options=options, service=service)
    driver.set_page_load_timeout(30)
    return driver