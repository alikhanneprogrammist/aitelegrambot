"""
Модуль для создания клавиатур Telegram бота
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton


def get_main_reply_keyboard():
    """Создает закрепленную клавиатуру с основными командами"""
    keyboard = [
        [
            KeyboardButton("📊 Продажи"),
            KeyboardButton("💰 Зарплаты")
        ],
        [
            KeyboardButton("🏠 Личные расходы"),
            KeyboardButton("🏢 Офисные расходы")
        ],
        [
            KeyboardButton("📈 Полный анализ"),
            KeyboardButton("✏️ Редактировать данные")
        ],
        [
            KeyboardButton("👥 Зарплаты сотрудников"),
            KeyboardButton("❓ Помощь")
        ],
        [
            KeyboardButton("📋 Главное меню")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True, one_time_keyboard=False)


def get_main_menu_keyboard():
    """Создает главное меню с основными вкладками"""
    keyboard = [
        [InlineKeyboardButton("📊 Продажи", callback_data="tab_sales")],
        [InlineKeyboardButton("💰 Зарплаты", callback_data="tab_salary")],
        [InlineKeyboardButton("🏠 Личные расходы", callback_data="tab_personal")],
        [InlineKeyboardButton("🏢 Офисные расходы", callback_data="tab_office")],
        [InlineKeyboardButton("❓ Помощь", callback_data="tab_help")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_sales_menu_keyboard():
    """Создает меню для раздела продаж"""
    keyboard = [
        [InlineKeyboardButton("📈 Быстрые инсайты", callback_data="sales_insights")],
        [InlineKeyboardButton("📊 Полный анализ", callback_data="sales_analyze")],
        [InlineKeyboardButton("💰 Прибыль за месяц", callback_data="sales_profit")],
        [InlineKeyboardButton("📋 Топ продажи", callback_data="sales_top")],
        [InlineKeyboardButton("🤖 AI рекомендации", callback_data="sales_ai_recommendations")],
        [InlineKeyboardButton("📈 Анализ трендов", callback_data="sales_trends")],
        [InlineKeyboardButton("✏️ Редактировать данные", callback_data="sales_edit")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_salary_menu_keyboard():
    """Создает меню для раздела зарплат"""
    keyboard = [
        [InlineKeyboardButton("🔄 Обновить зарплаты", callback_data="salary_update")],
        [InlineKeyboardButton("💰 Показать зарплаты", callback_data="salary_show")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_office_menu_keyboard():
    """Создает меню для раздела офисных расходов"""
    keyboard = [
        [InlineKeyboardButton("🏢 Офисные расходы", callback_data="office_show")],
        [InlineKeyboardButton("➕ Добавить офисный расход", callback_data="office_add")],
        [InlineKeyboardButton("📊 Сводка офисных расходов", callback_data="office_summary")],
        [InlineKeyboardButton("💰 Прибыль с учетом офиса", callback_data="office_profit")],
        [InlineKeyboardButton("📋 Добавить константы", callback_data="office_constants")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_personal_expenses_menu_keyboard():
    """Создает меню для личных расходов"""
    keyboard = [
        [InlineKeyboardButton("🎤 Добавить расход (голос)", callback_data="personal_add_voice")],
        [InlineKeyboardButton("✏️ Добавить расход (текст)", callback_data="personal_add_text")],
        [InlineKeyboardButton("📋 Последние расходы", callback_data="personal_recent")],
        [InlineKeyboardButton("✏️ Исправить последний расход", callback_data="personal_edit_last")],
        [InlineKeyboardButton("📊 Сводка за неделю", callback_data="personal_weekly")],
        [InlineKeyboardButton("📈 Сводка за месяц", callback_data="personal_summary")],
        [InlineKeyboardButton("🤖 GPT Анализ трат", callback_data="personal_gpt_analysis")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_office_expenses_menu_keyboard():
    """Создает меню для офисных расходов"""
    keyboard = [
        [InlineKeyboardButton("🎤 Добавить расход (голос)", callback_data="office_add_voice")],
        [InlineKeyboardButton("✏️ Добавить расход (текст)", callback_data="office_add_text")],
        [InlineKeyboardButton("📋 Последние расходы", callback_data="office_recent")],
        [InlineKeyboardButton("✏️ Исправить последний расход", callback_data="office_edit_last")],
        [InlineKeyboardButton("📊 Сводка за неделю", callback_data="office_weekly")],
        [InlineKeyboardButton("📈 Сводка за месяц", callback_data="office_summary")],
        [InlineKeyboardButton("🤖 GPT Анализ трат", callback_data="office_gpt_analysis")],
        [InlineKeyboardButton("🔙 Назад в главное меню", callback_data="main_menu")]
    ]
    return InlineKeyboardMarkup(keyboard)
