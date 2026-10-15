"""
Константы проекта: URL, таймауты, data-test поля.
"""

from runtime import LOGIN_FILE, DATA_FILE  # noqa: F401  (реэкспорт для io_utils)

# --- URL формы ---
FORM_URL = "https://help.ranepa.ru/record/itsm_spb_personal_task"

# --- Таймауты (секунды). Везде — минимум, достаточный для реакции UI ---
TIMEOUT_LOGIN_FIELD = 7
TIMEOUT_DEFAULT = 6
TIMEOUT_DROPDOWN = 8
TIMEOUT_SELECT = 8
TIMEOUT_SHORT = 0.5
TIMEOUT_FORM_AFTER_LOGIN = 7
POLL_FAST = 0.03

# --- data-test идентификаторы полей формы ---
FIELD_CALLER = "caller-field-reference"
FIELD_ASSIGNMENT_GROUP = "assignment_group-field-reference"
FIELD_ASSIGNED_USER = "assigned_user-field-reference"
FIELD_STATUS = "state-field-select"
FIELD_URGENCY = "urgency-field-select"

FIELD_SUBJECT_IDS = ["subject-field-textarea"]
FIELD_DESCRIPTION_RICH = "description_ptsk-field-rich-text"

# --- Значения для выбора ---
STATUS_VALUE = "В работе"
URGENCY_VALUE = "Низкая"

# --- Тексты для темы и описания ---
SUBJECT_TEXT = "П/2 Сопровождение учебного процесса"
DESCRIPTION_TEXT = "Сопровождение учебного процесса."

# --- Кнопки входа (по тексту) ---
LOGIN_BUTTON_TEXTS = [
    'Войти', 'Вход', 'Login', 'Sign in',
    'Продолжить', 'Continue', 'Далее',
]

# --- Общее количество полей для отчёта ---
TOTAL_FIELDS = 8

# --- Повторные проходы по полям ---
FIELD_RETRY_ATTEMPTS = 3          # сколько раз пробовать поле
FIELD_RETRY_DELAY = 0.6           # пауза между попытками

# --- Параллелизм ---
MAX_PARALLEL = 10
LOCK_TIMEOUT = 120