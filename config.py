"""
Конфигурационный файл для бота
"""

# Конфигурация колонок Excel
COLUMN_MAPPINGS = {
    'price': ['price', 'сумма', 'стоимость', 'total', 'amount'],
    'manager': ['manager', 'менеджер'],
    'rop': ['employee ROP', 'rop', 'РОП'],
    'order': ['order', 'заказ', 'номер_заказа'],
    'quantity': ['quantity', 'количество', 'кол-во'],
    'product': ['name_boiler', 'товар', 'наименование', 'продукт']
}

# Ключевые слова для распознавания намерений
INTENT_KEYWORDS = {
    'edit': [
        'изменить', 'изменение', 'поменять', 'исправить', 'обновить',
        'заказ', 'заказе', 'котел', 'котлы', 'количество', 'цена', 'цену',
        'вместо', 'взял', 'заказал', 'нужно', 'надо', 'менеджер', 'менеджера'
    ],
    'analysis': [
        'анализ', 'проанализируй', 'статистика', 'отчет', 'данные',
        'продажи', 'выручка', 'прибыль', 'показатели'
    ],
    'insights': [
        'инсайты', 'быстро', 'кратко', 'сводка', 'итоги'
    ],
    'update': [
        'обновить зарплаты', 'зарплата', 'бонус', 'расчет', 'пересчитать'
    ]
}

# Настройки кэширования
CACHE_DURATION = 300  # 5 минут в секундах
MAX_CACHE_SIZE = 10   # максимум файлов в кэше

# Настройки Excel
EXCEL_SHEET_NAMES = {
    'sales': 'продажи',
    'salary': 'зарплата'
}

# Лимиты для ответов
MAX_MESSAGE_LENGTH = 4000
MAX_ANALYSIS_RECORDS = 10

# Настройки бота
BOT_SETTINGS = {
    'poll_interval': 1.0,
    'timeout': 10,
    'read_timeout': 10,
    'write_timeout': 10,
    'connect_timeout': 10,
    'pool_timeout': 10
}

# Пути к файлам
FILE_PATHS = {
    'excel_file': 'Alseit.xlsx',
    'expenses_file': 'expenses.xlsx',
    'log_file': 'bot.log'
}

# Настройки логирования
LOGGING_CONFIG = {
    'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'level': 'INFO',
    'handlers': ['console', 'file']
}

# Настройки Telegram
TELEGRAM_SETTINGS = {
    'max_message_length': 4000,
    'parse_mode': 'Markdown'
}