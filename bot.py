import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, filters, ContextTypes
from salary_folder.salary_update import update_salary
from sales_folder.chatgpt_analyzer import ChatGPTAnalyzer
from sales_folder.voice_handler import VoiceHandler
from sales_folder.ai_recommendations import AIRecommendations
from personal_expenses.expense_manager import PersonalExpenseManager
from office_expenses.expense_manager import OfficeExpenseManager
from dotenv import load_dotenv
from utils import data_cache, get_gross_profit, get_net_profit, get_net_profit_from_sales, get_office_expenses_total, get_office_summary, add_office_constants, split_message_if_long, load_excel_with_cache

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXCEL_FILE = os.getenv("EXCEL_FILE_NAME", "Alseit.xlsx")

# Инициализируем ChatGPT анализатор
try:
    chatgpt_analyzer = ChatGPTAnalyzer()
    CHATGPT_AVAILABLE = True
except Exception as e:
    print(f"⚠️ ChatGPT недоступен: {e}")
    CHATGPT_AVAILABLE = False

# Инициализируем обработчик голосовых сообщений
try:
    voice_handler = VoiceHandler()
    VOICE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Голосовой обработчик недоступен: {e}")
    VOICE_AVAILABLE = False

# Инициализируем новые модули


try:
    excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
    ai_recommendations = AIRecommendations(excel_path)
    AI_RECOMMENDATIONS_AVAILABLE = True
except Exception as e:
    print(f"⚠️ AI рекомендации недоступны: {e}")
    AI_RECOMMENDATIONS_AVAILABLE = False

# Инициализируем менеджеры расходов
try:
    expenses_file = os.path.join(os.path.dirname(__file__), "expenses.xlsx")
    personal_expense_manager = PersonalExpenseManager(expenses_file)
    office_expense_manager = OfficeExpenseManager(expenses_file)
    EXPENSES_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Менеджеры расходов недоступны: {e}")
    EXPENSES_AVAILABLE = False

# Импортируем клавиатуры из отдельного модуля
from keyboards import (
    get_main_reply_keyboard, get_main_menu_keyboard, get_sales_menu_keyboard,
    get_salary_menu_keyboard, get_office_menu_keyboard, 
    get_personal_expenses_menu_keyboard, get_office_expenses_menu_keyboard
)




# === ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ===

async def safe_edit_message(query, text, reply_markup=None, parse_mode='Markdown'):
    """
    Безопасное редактирование сообщения с обработкой ошибок
    
    Args:
        query: CallbackQuery объект от Telegram
        text (str): Текст для отображения
        reply_markup: Клавиатура для отображения
        parse_mode (str): Режим парсинга (Markdown/HTML)
    
    Returns:
        None
    """
    try:
        await query.edit_message_text(
            text=text,
            reply_markup=reply_markup,
            parse_mode=parse_mode
        )
    except Exception as e:
        # Если не удалось отредактировать сообщение, отправляем новое
        try:
            await query.message.reply_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
        except Exception as e2:
            # В крайнем случае отправляем простое сообщение
            await query.message.reply_text(f"❌ Ошибка отображения: {str(e2)}")

# Импортируем обработчики команд из отдельного модуля
from command_handlers import CommandHandler as BotCommandHandler

# Создаем экземпляр обработчика команд
command_handler = BotCommandHandler(chatgpt_analyzer if CHATGPT_AVAILABLE else None)



# === ОБРАБОТЧИКИ CALLBACK ЗАПРОСОВ (ВКЛАДКИ) ===

async def button_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик нажатий на кнопки вкладок
    
    Обрабатывает все callback запросы от inline клавиатур,
    включая навигацию по меню и выполнение различных действий.
    
    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст бота
    
    Returns:
        None
    """
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Главное меню
    if data == "main_menu":
        chatgpt_status = "✅ Доступен" if CHATGPT_AVAILABLE else "❌ Недоступен"
        voice_status = "✅ Доступен" if VOICE_AVAILABLE else "❌ Недоступен"
        
        welcome_text = (
            f"🤖 Главное меню\n\n"
            f"📊 ChatGPT AI: {chatgpt_status}\n"
            f"🎤 Голосовые команды: {voice_status}\n\n"
            f"🎯 **ВЫБЕРИТЕ РАЗДЕЛ** для работы:"
        )
        
        await safe_edit_message(
            query=query,
            text=welcome_text,
            reply_markup=get_main_menu_keyboard()
        )
    
    # Раздел продаж
    elif data == "tab_sales":
        await safe_edit_message(
            query=query,
            text="📊 **ПРОДАЖИ**\n\nВыберите действие:",
            reply_markup=get_sales_menu_keyboard()
        )
    
    # Раздел зарплат
    elif data == "tab_salary":
        await safe_edit_message(
            query=query,
            text="💰 **ЗАРПЛАТЫ**\n\nВыберите действие:",
            reply_markup=get_salary_menu_keyboard()
        )
    
    # Раздел личных расходов
    elif data == "tab_personal":
        await safe_edit_message(
            query=query,
            text="🏠 **ЛИЧНЫЕ РАСХОДЫ**\n\nВыберите действие:",
            reply_markup=get_personal_expenses_menu_keyboard()
        )
    
    # Раздел офисных расходов
    elif data == "tab_office":
        await safe_edit_message(
            query=query,
            text="🏢 **ОФИСНЫЕ РАСХОДЫ**\n\nВыберите действие:",
            reply_markup=get_office_expenses_menu_keyboard()
        )
    
    
    
    # Раздел помощи
    elif data == "tab_help":
        help_text = """
🤖 **СПРАВКА ПО БОТУ**

📊 **ПРОДАЖИ И ЗАРПЛАТЫ**:
• Обновление зарплат и расчет бонусов
• Анализ продаж и эффективности
• Редактирование данных через AI
• Быстрые инсайты и отчеты


🤖 **AI АНАЛИЗ**:
• Умный анализ данных
• Редактирование через естественный язык
• Голосовые команды
• Генерация отчетов

⚙️ **НАСТРОЙКИ**:
• Конфигурация бота
• Настройки расходов
• Параметры продаж

💡 **ПРИМЕРЫ КОМАНД**:
• "Сколько заказов у менеджера Иван?"
• "Добавить расход еда 5000 ресторан"
• "Показать расходы за месяц"
• "Проверить лимиты расходов"
        """
        await safe_edit_message(
            query=query,
            text=help_text,
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton("🔙 Назад в главное меню", callback_data="main_menu")
            ]])
        )
    
    # === ОБРАБОТЧИКИ ДЛЯ РАЗДЕЛА ПРОДАЖ ===
    elif data == "sales_update":
        try:
            result = update_salary()
            await safe_edit_message(
                query=query,
                text=f"🔄 ОБНОВЛЕНИЕ ЗАРПЛАТ\n\n{result}",
                reply_markup=get_sales_menu_keyboard(),
                parse_mode=None
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {e}",
                reply_markup=get_sales_menu_keyboard()
            )
    
    elif data == "sales_insights":
        try:
            excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
            insights = chatgpt_analyzer.get_quick_insights(excel_path)
            await safe_edit_message(
                query=query,
                text=f"📈 **БЫСТРЫЕ ИНСАЙТЫ**\n\n{insights}",
                reply_markup=get_sales_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_sales_menu_keyboard()
            )
    
    elif data == "sales_analyze":
        if not CHATGPT_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ ChatGPT AI недоступен. Проверьте настройки API ключа.",
                reply_markup=get_sales_menu_keyboard()
            )
            return
        
        # Логируем начало анализа
        logging.info("🔄 Начинаем полный анализ продаж...")
        print("🔄 Начинаем полный анализ продаж...")
        
        await safe_edit_message(
            query=query,
            text="🔄 Анализирую данные... Это может занять несколько секунд.",
            reply_markup=get_sales_menu_keyboard()
        )
        
        try:
            excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
            # Безопасное логирование - не выводим полный путь
            logging.info("📁 Загружаем Excel файл для анализа")
            print("📁 Загружаем Excel файл для анализа")
            
            # Проверяем существование файла
            if not os.path.exists(excel_path):
                error_msg = "❌ Excel файл не найден"
                logging.error("Excel файл не найден")
                print("Excel файл не найден")
                await safe_edit_message(
                    query=query,
                    text=error_msg,
                    reply_markup=get_sales_menu_keyboard()
                )
                return
            
            logging.info("🤖 Вызываем ChatGPT анализатор...")
            print("🤖 Вызываем ChatGPT анализатор...")
            
            analysis = chatgpt_analyzer.analyze_sales_data(excel_path)
            
            logging.info(f"✅ Анализ получен, длина: {len(analysis)} символов")
            print(f"✅ Анализ получен, длина: {len(analysis)} символов")
            
            if len(analysis) > 4000:
                analysis = analysis[:4000] + "\n\n... (сообщение обрезано)"
                logging.info("✂️ Сообщение обрезано до 4000 символов")
                print("✂️ Сообщение обрезано до 4000 символов")
            
            # Экранируем символы Markdown для безопасного отображения
            safe_analysis = analysis.replace('*', '\\*').replace('_', '\\_').replace('[', '\\[').replace(']', '\\]')
            
            logging.info("📊 Отправляем результат анализа...")
            print("📊 Отправляем результат анализа...")
            
            await safe_edit_message(
                query=query,
                text=f"📊 **AI АНАЛИЗ ДАННЫХ**\n\n{safe_analysis}",
                reply_markup=get_sales_menu_keyboard()
            )
            
            logging.info("✅ Анализ успешно отправлен")
            print("✅ Анализ успешно отправлен")
            
        except Exception as e:
            error_msg = f"❌ Ошибка при анализе: {str(e)}"
            logging.error(error_msg)
            print(error_msg)
            await safe_edit_message(
                query=query,
                text=error_msg,
                reply_markup=get_sales_menu_keyboard()
            )
    
    elif data == "sales_profit":
        try:
            # Получаем чистую прибыль от продаж (без офисных расходов)
            net_profit_from_sales = get_net_profit_from_sales()
            office_expenses = get_office_expenses_total()
            
            # Итоговая прибыль за месяц = чистая прибыль от продаж - офисные расходы
            monthly_profit = net_profit_from_sales - office_expenses
            
            profit_text = f"💰 **ПРИБЫЛЬ ЗА МЕСЯЦ**\n\n"
            profit_text += f"📊 Чистая прибыль от продаж: {net_profit_from_sales:,.0f} тенге\n"
            profit_text += f"🏢 Офисные расходы: {office_expenses:,.0f} тенге\n"
            profit_text += f"💸 Итоговая прибыль за месяц: {monthly_profit:,.0f} тенге\n\n"
            
            # Проверяем, чтобы избежать деления на ноль
            if net_profit_from_sales > 0:
                profitability = (monthly_profit / net_profit_from_sales * 100)
                profit_text += f"📈 Рентабельность: {profitability:.1f}%"
            else:
                profit_text += f"📈 Рентабельность: Н/Д (нет прибыли от продаж)"
            
            await safe_edit_message(
                query=query,
                text=profit_text,
                reply_markup=get_sales_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_sales_menu_keyboard()
            )
    
    elif data == "sales_top":
        try:
            if not CHATGPT_AVAILABLE:
                await safe_edit_message(
                    query=query,
                    text="❌ ChatGPT AI недоступен для анализа топ продаж.",
                    reply_markup=get_sales_menu_keyboard()
                )
                return
            
            excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
            # Запрашиваем анализ топ продаж
            top_analysis = chatgpt_analyzer.analyze_sales_data(excel_path, focus="top_sales")
            
            if len(top_analysis) > 4000:
                top_analysis = top_analysis[:4000] + "\n\n... (сообщение обрезано)"
            
            await safe_edit_message(
                query=query,
                text=f"📋 **ТОП ПРОДАЖИ**\n\n{top_analysis}",
                reply_markup=get_sales_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_sales_menu_keyboard()
            )
    
    
    
    elif data == "sales_ai_recommendations":
        try:
            if not AI_RECOMMENDATIONS_AVAILABLE:
                await safe_edit_message(
                    query=query,
                    text="❌ AI рекомендации недоступны.",
                    reply_markup=get_sales_menu_keyboard()
                )
                return
            
            recommendations = ai_recommendations.get_ai_recommendations("sales")
            await safe_edit_message(
                query=query,
                text=f"🤖 **AI РЕКОМЕНДАЦИИ ПО ПРОДАЖАМ**\n\n{recommendations}",
                reply_markup=get_sales_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_sales_menu_keyboard()
            )
    
    elif data == "sales_trends":
        try:
            if not AI_RECOMMENDATIONS_AVAILABLE:
                await safe_edit_message(
                    query=query,
                    text="❌ Анализ трендов недоступен.",
                    reply_markup=get_sales_menu_keyboard()
                )
                return
            
            trends = ai_recommendations.analyze_trends_and_patterns(6)
            if trends['status'] == 'success':
                text = f"📈 **АНАЛИЗ ТРЕНДОВ И ЗАКОНОМЕРНОСТЕЙ**\n\n"
                text += f"📅 Период анализа: {trends['analysis_period']}\n\n"
                
                if 'patterns' in trends and trends['patterns'].get('status') != 'error':
                    patterns = trends['patterns']
                    text += f"📊 **Выявленные закономерности:**\n"
                    text += f"• Тренд роста: {patterns.get('growth_trend', 'Неизвестно')}\n"
                    text += f"• Средний рост: {patterns.get('avg_growth_rate', 0):.1f}%\n"
                    text += f"• Стабильность: {patterns.get('stability', 'Неизвестно')}\n\n"
                
                if 'trends' in trends and trends['trends'].get('status') != 'error':
                    trends_data = trends['trends']
                    text += f"📈 **Тренды:**\n"
                    text += f"• Продажи: {trends_data.get('sales_trend', {}).get('direction', 'Неизвестно')}\n"
                    text += f"• Заказы: {trends_data.get('orders_trend', {}).get('direction', 'Неизвестно')}\n"
                    text += f"• Средний чек: {trends_data.get('avg_order_trend', {}).get('direction', 'Неизвестно')}\n"
            else:
                text = f"❌ {trends.get('message', 'Ошибка анализа трендов')}"
            
            await safe_edit_message(
                query=query,
                text=text,
                reply_markup=get_sales_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_sales_menu_keyboard()
            )
    
    # Обработчик для кнопки "✏️ Редактировать данные"
    elif data == "sales_edit":
        await safe_edit_message(
            query=query,
            text="✏️ РЕДАКТИРОВАНИЕ ДАННЫХ ПРОДАЖ\n\nДля редактирования данных используйте команду /edit или напишите:\n\n• 'Изменить продажу номер X'\n• 'Добавить новую продажу'\n• 'Удалить запись номер X'\n\nПримеры:\n• 'Изменить продажу номер 5 - цена 500000'\n• 'Добавить продажу: клиент Иванов, котел alseit_25, цена 400000'\n• 'Удалить запись номер 3'",
            reply_markup=get_sales_menu_keyboard(),
            parse_mode=None
        )
    
    
    # === ОБРАБОТЧИКИ ДЛЯ РАЗДЕЛА ЗАРПЛАТ ===
    elif data == "salary_update":
        try:
            result = update_salary()
            await safe_edit_message(
                query=query,
                text=f"🔄 ОБНОВЛЕНИЕ ЗАРПЛАТ\n\n{result}",
                reply_markup=get_salary_menu_keyboard(),
                parse_mode=None
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {e}",
                reply_markup=get_salary_menu_keyboard()
            )
    
    elif data == "salary_show":
        try:
            from salary_folder.salary_update import get_salary_summary
            result = get_salary_summary()
            await safe_edit_message(
                query=query,
                text=result,
                reply_markup=get_salary_menu_keyboard(),
                parse_mode=None
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {e}",
                reply_markup=get_salary_menu_keyboard()
            )
    
    elif data == "salary_monthly":
        try:
            # Получаем информацию о зарплатах за месяц
            gross_profit = get_gross_profit()
            net_profit = get_net_profit()
            office_expenses = get_office_expenses_total()
            
            salary_text = f"💰 **ЗАРПЛАТЫ ЗА МЕСЯЦ**\n\n"
            salary_text += f"📊 Валовая прибыль: {gross_profit:,.0f} тенге\n"
            salary_text += f"🏢 Офисные расходы: {office_expenses:,.0f} тенге\n"
            salary_text += f"💸 Чистая прибыль: {net_profit:,.0f} тенге\n\n"
            salary_text += f"💡 Чистая прибыль доступна для выплаты зарплат"
            
            await safe_edit_message(
                query=query,
                text=salary_text,
                reply_markup=get_salary_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_salary_menu_keyboard()
            )
    
    # === ОБРАБОТЧИКИ ДЛЯ РАЗДЕЛА ОФИСНЫХ РАСХОДОВ ===
    elif data == "office_show":
        try:
            summary = get_office_summary()
            await safe_edit_message(
                query=query,
                text=f"🏢 **ОФИСНЫЕ РАСХОДЫ**\n\n{summary}",
                reply_markup=get_office_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_office_menu_keyboard()
            )
    
    elif data == "office_summary":
        try:
            summary = get_office_summary()
            await safe_edit_message(
                query=query,
                text=f"📊 **СВОДКА ОФИСНЫХ РАСХОДОВ**\n\n{summary}",
                reply_markup=get_office_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_office_menu_keyboard()
            )
    
    elif data == "office_profit":
        try:
            gross_profit = get_gross_profit()
            net_profit = get_net_profit()
            office_expenses = get_office_expenses_total()
            
            profit_text = f"💰 **ПРИБЫЛЬ С УЧЕТОМ ОФИСА**\n\n"
            profit_text += f"📊 Валовая прибыль: {gross_profit:,.0f} тенге\n"
            profit_text += f"🏢 Офисные расходы: {office_expenses:,.0f} тенге\n"
            profit_text += f"💸 Чистая прибыль: {net_profit:,.0f} тенге\n\n"
            
            # Проверяем, чтобы избежать деления на ноль
            if gross_profit > 0:
                efficiency = (net_profit / gross_profit * 100)
                profit_text += f"📈 Эффективность: {efficiency:.1f}%"
            else:
                profit_text += f"📈 Эффективность: Н/Д (нет валовой прибыли)"
            
            await safe_edit_message(
                query=query,
                text=profit_text,
                reply_markup=get_office_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_office_menu_keyboard()
            )
    
    elif data == "office_constants":
        try:
            result = add_office_constants()
            await safe_edit_message(
                query=query,
                text=f"📋 **ДОБАВЛЕНИЕ ОФИСНЫХ КОНСТАНТ**\n\n{result}",
                reply_markup=get_office_menu_keyboard()
            )
        except Exception as e:
            await safe_edit_message(
                query=query,
                text=f"❌ Ошибка: {str(e)}",
                reply_markup=get_office_menu_keyboard()
            )
    
    # === ОБРАБОТЧИКИ ДЛЯ ОФИСНЫХ РАСХОДОВ ===
    elif data == "office_add_voice":
        await safe_edit_message(
            query=query,
            text="🎤 **ДОБАВЛЕНИЕ ОФИСНОГО РАСХОДА**\n\n"
                 "Отправьте голосовое сообщение с описанием расхода.\n"
                 "Например: \"Купил канцелярию на 5000\" или \"Оплатил интернет 25000\"",
            reply_markup=get_office_expenses_menu_keyboard()
        )
    
    elif data == "office_add_text":
        await safe_edit_message(
            query=query,
            text="✏️ **ДОБАВЛЕНИЕ ОФИСНОГО РАСХОДА**\n\n"
                 "Напишите расход в формате:\n"
                 "• \"5000 канцелярия ручки\"\n"
                 "• \"25000 связь интернет\"\n"
                 "• \"15000 уборка офиса\"",
            reply_markup=get_office_expenses_menu_keyboard()
        )
    
    # === ОБРАБОТЧИКИ ДЛЯ ЛИЧНЫХ РАСХОДОВ ===
    elif data == "personal_add_voice":
        await safe_edit_message(
            query=query,
            text="🎤 **ДОБАВЛЕНИЕ ЛИЧНОГО РАСХОДА**\n\n"
                 "Отправьте голосовое сообщение с описанием расхода.\n"
                 "Например: \"Потратил 5000 в кафе\" или \"Купил продукты на 15000\"",
            reply_markup=get_personal_expenses_menu_keyboard()
        )
    
    elif data == "personal_add_text":
        await safe_edit_message(
            query=query,
            text="✏️ **ДОБАВЛЕНИЕ ЛИЧНОГО РАСХОДА**\n\n"
                 "Напишите расход в формате:\n"
                 "• \"5000 еда кафе\"\n"
                 "• \"15000 транспорт такси\"\n"
                 "• \"3000 развлечения кино\"",
            reply_markup=get_personal_expenses_menu_keyboard()
        )
    
    elif data == "personal_summary":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                # Добавляем постоянные расходы если нужно
                personal_expense_manager.add_fixed_expenses_if_needed()
                summary = personal_expense_manager.get_monthly_summary()
                await safe_edit_message(
                    query=query,
                    text=summary,
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    elif data == "personal_categories":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                summary = personal_expense_manager.get_category_breakdown()
                await safe_edit_message(
                    query=query,
                    text=summary,
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    elif data == "personal_recent":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                recent = personal_expense_manager.get_recent_expenses()
                await safe_edit_message(
                    query=query,
                    text=recent,
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    elif data == "personal_weekly":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                weekly = personal_expense_manager.get_weekly_summary()
                await safe_edit_message(
                    query=query,
                    text=weekly,
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    elif data == "personal_gpt_analysis":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                analysis = personal_expense_manager.get_gpt_analysis()
                await safe_edit_message(
                    query=query,
                    text=analysis,
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    elif data == "personal_edit_last":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                # Исправляем последний расход: меняем категорию с "еда" на "кафе" и сумму с 150 на 150000
                success, message = personal_expense_manager.edit_last_expense(new_category="кафе", new_amount=150000)
                await safe_edit_message(
                    query=query,
                    text=f"✏️ **ИСПРАВЛЕНИЕ ПОСЛЕДНЕГО РАСХОДА**\n\n{message}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    elif data == "personal_total":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_personal_expenses_menu_keyboard()
            )
        else:
            try:
                summary = personal_expense_manager.get_monthly_summary()
                await safe_edit_message(
                    query=query,
                    text=summary,
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_personal_expenses_menu_keyboard()
                )
    
    
    elif data == "office_summary":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                # Добавляем постоянные расходы если нужно
                office_expense_manager.add_fixed_expenses_if_needed()
                summary = office_expense_manager.get_monthly_summary()
                await safe_edit_message(
                    query=query,
                    text=summary,
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
    
    elif data == "office_categories":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                summary = office_expense_manager.get_category_breakdown()
                await safe_edit_message(
                    query=query,
                    text=summary,
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
    
    elif data == "office_total":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                summary = office_expense_manager.get_monthly_summary()
                await safe_edit_message(
                    query=query,
                    text=summary,
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
    
    elif data == "office_recent":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                recent = office_expense_manager.get_recent_expenses()
                await safe_edit_message(
                    query=query,
                    text=recent,
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
    
    elif data == "office_weekly":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                weekly = office_expense_manager.get_weekly_summary()
                await safe_edit_message(
                    query=query,
                    text=weekly,
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
    
    elif data == "office_gpt_analysis":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                analysis = office_expense_manager.get_gpt_analysis()
                await safe_edit_message(
                    query=query,
                    text=analysis,
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
    
    elif data == "office_edit_last":
        if not EXPENSES_AVAILABLE:
            await safe_edit_message(
                query=query,
                text="❌ Менеджер расходов недоступен",
                reply_markup=get_office_expenses_menu_keyboard()
            )
        else:
            try:
                # Показываем информацию о последнем расходе и предлагаем исправить
                recent = office_expense_manager.get_recent_expenses(limit=1)
                await safe_edit_message(
                    query=query,
                    text=f"✏️ **ИСПРАВЛЕНИЕ ПОСЛЕДНЕГО ОФИСНОГО РАСХОДА**\n\n{recent}\n\nДля исправления используйте команду: 'исправить категорию на [новая_категория]' или 'исправить сумму на [новая_сумма]'",
                    reply_markup=get_office_expenses_menu_keyboard()
                )
            except Exception as e:
                await safe_edit_message(
                    query=query,
                    text=f"❌ Ошибка: {str(e)}",
                    reply_markup=get_office_expenses_menu_keyboard()
                )

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Обработчик голосовых сообщений
    
    Обрабатывает голосовые сообщения пользователей,
    распознает речь и выполняет соответствующие команды.
    
    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст бота
    
    Returns:
        None
    """
    if not VOICE_AVAILABLE:
        await update.message.reply_text(
            "❌ Голосовые команды недоступны.\n\n"
            "🔧 **Для работы с голосовыми сообщениями нужно:**\n"
            "1. Установить ffmpeg\n"
            "2. Или использовать текстовые команды\n\n"
            "💡 **Альтернативы:**\n"
            "• Напишите команду текстом\n"
            "• Используйте кнопки в меню\n"
            "• Обратитесь к /help для справки"
        )
        return
    
    try:
        # Отправляем сообщение о начале обработки
        processing_message = await update.message.reply_text("🎤 Обрабатываю голосовое сообщение...")
        
        # Получаем голосовой файл
        voice_file = await update.message.voice.get_file()
        
        # Обрабатываем голосовое сообщение
        recognized_text = await voice_handler.process_voice_message(voice_file)
        
        # Обновляем сообщение с результатом распознавания
        if recognized_text.startswith("❌"):
            # Ошибка распознавания - показываем полное сообщение об ошибке
            await processing_message.edit_text(recognized_text)
            return
        
        # Показываем распознанный текст
        await processing_message.edit_text(f"🎤 Распознанный текст: \"{recognized_text}\"")
        
        # Анализируем голосовую команду
        command_data = voice_handler.parse_voice_command(recognized_text)
        
        if not command_data.get('success'):
            await update.message.reply_text(f"❌ Не удалось понять команду: {command_data.get('error', 'Неизвестная ошибка')}")
            return
        
        # Создаем текстовую команду для существующего обработчика
        text_command = voice_handler.create_text_command(command_data)
        
        if not text_command:
            await update.message.reply_text("❌ Не удалось преобразовать голосовую команду в текстовую")
            return
        
        # Отправляем сообщение о выполнении команды
        await update.message.reply_text(f"🤖 Выполняю команду: \"{text_command}\"")
        
        # Определяем тип команды и вызываем соответствующий обработчик
        if command_data.get('action') == 'edit_order':
            # Имитируем context.args для edit_handler
            context.args = text_command.split()
            await command_handler.edit_command(update, context)
        elif command_data.get('action') == 'add_multiple_expenses':
            # Обрабатываем добавление множественных расходов
            if EXPENSES_AVAILABLE:
                expenses = command_data.get('expenses', [])
                results = []
                
                for expense in expenses:
                    expense_type = expense.get('expense_type', 'personal')
                    amount = expense.get('amount', 0)
                    category = expense.get('category', 'другое')
                    description = expense.get('description', '')
                    
                    # Создаем текст для добавления расхода
                    expense_text = f"потратил {amount} на {category}"
                    if description:
                        expense_text += f" ({description})"
                    
                    if expense_type == 'personal':
                        success, message = personal_expense_manager.add_expense_from_voice(expense_text)
                        results.append(f"🏠 {message}")
                    else:  # office
                        success, message = office_expense_manager.add_expense_from_voice(expense_text)
                        results.append(f"🏢 {message}")
                
                # Отправляем все результаты
                await update.message.reply_text("\n".join(results))
            else:
                await update.message.reply_text("❌ Менеджеры расходов недоступны")
        else:
            # Используем универсальный обработчик для других команд
            # Создаем Mock объект для имитации текстового сообщения
            class MockMessage:
                def __init__(self, text, original_message):
                    self.text = text
                    self.original_message = original_message
                    self.chat = original_message.chat
                    self.from_user = original_message.from_user
                    self.message_id = original_message.message_id
                    self.date = original_message.date
                    
                async def reply_text(self, text):
                    return await self.original_message.reply_text(text)
            
            class MockUpdate:
                def __init__(self, message):
                    self.message = message
                    self.update_id = update.update_id
                    self.effective_chat = update.effective_chat
                    self.effective_user = update.effective_user
            
            # Создаем mock объекты
            mock_message = MockMessage(text_command, update.message)
            mock_update = MockUpdate(mock_message)
            
            await smart_message_handler(mock_update, context)
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обработке голосового сообщения: {str(e)}")

async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Справка по командам"""
    help_text = """
🤖 ФИНАНСОВЫЙ БОТ - СПРАВКА

📊 ОСНОВНЫЕ КОМАНДЫ:
• /start - начать работу с ботом
• /update - обновить зарплаты и рассчитать бонусы
• /analyze - полный AI анализ данных (Gemini)
• /insights - быстрые инсайты по продажам
• /edit - редактировать данные в Excel (AI)
• /refresh - обновить данные из Excel
• /ask - быстрый вопрос о данных
• /help - эта справка


⌨️ КЛАВИАТУРА:
• /show - показать закрепленные кнопки
• /hide - скрыть закрепленные кнопки

🔧 НАСТРОЙКИ:
• Убедитесь, что файл Alseit.xlsx находится в папке с ботом
• Для AI анализа нужен GEMINI_API_KEY в .env файле

📈 ЧТО ДЕЛАЕТ БОТ:
• Автоматически рассчитывает НДС (16%)
• Вычисляет стоимость доставки
• Рассчитывает бонусы менеджеров (5%) и ROP (1%)
• Создает сводки в Excel
• Анализирует данные с помощью AI
• Редактирует данные в Excel через естественный язык
• Автоматически отслеживает изменения в Excel файле
• Отвечает на ЛЮБЫЕ вопросы о ваших данных!
• Управляет личными расходами с проверкой лимитов

🤖 ПРИМЕРЫ УМНЫХ ЗАПРОСОВ:
• "Сколько заказов у менеджера Анна?"
• "Какой товар приносит больше всего прибыли?"
• "Покажи все заказы клиента ТОО Строй"
• "Средняя сумма продаж в январе"
• "Сравни эффективность менеджеров"
• "Найди самые дорогие заказы"
• "Статистика по дням недели"

💰 ПРИМЕРЫ ЛИЧНЫХ РАСХОДОВ:
• "Добавить расход еда 5000 ресторан"
• "Показать расходы за месяц"
• "Проверить лимиты расходов"
• "Добавить месячные константы"

🎤 ГОЛОСОВЫЕ КОМАНДЫ:
• "Измени количество котлов 3 штуки в номере заказа 2"
• "Поменяй цену в заказе 5 на 50000"
• "Назначь менеджером Иван в заказе 3"
• "Сколько заказов у менеджера Анна?"
• "Какой средний чек за неделю?"

⚠️ ВАЖНО: Для работы голосовых команд нужен ffmpeg:
`conda install ffmpeg -c conda-forge`

📝 ПРИМЕРЫ РЕДАКТИРОВАНИЯ:



• /edit заказ номер #2 вместо двух котлов взял один
• /edit изменить количество товара 'котлы' в заказе 5 с 3 на 1
• /edit обновить цену товара в заказе 1 на 50000
• /edit назначить менеджером Иван в заказе 3


    """
    await update.message.reply_text(help_text)

async def smart_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Умный обработчик сообщений - автоматически определяет намерения пользователя
    
    Анализирует текстовые сообщения пользователей и определяет их намерения
    на основе ключевых слов, затем направляет к соответствующему обработчику.
    
    Args:
        update (Update): Объект обновления от Telegram
        context (ContextTypes.DEFAULT_TYPE): Контекст бота
    
    Returns:
        None
    """
    message_text = update.message.text
    
    # Сначала проверяем, является ли это кнопкой
    if message_text in [
        "📊 Продажи", "💰 Зарплаты", "🏠 Личные расходы", "🏢 Офисные расходы",
        "📈 Полный анализ", "✏️ Редактировать данные", "🔄 Обновить данные", 
        "❓ Помощь", "📋 Главное меню"
    ]:
        await handle_reply_buttons(update, context)
        return
    
    # Если не кнопка, обрабатываем как обычное сообщение
    message_text_lower = message_text.lower()
    
    # Ключевые слова для редактирования
    edit_keywords = [
        'изменить', 'изменение', 'поменять', 'исправить', 'обновить',
        'заказ', 'заказе', 'котел', 'котлы', 'количество', 'цена', 'цену',
        'вместо', 'взял', 'заказал', 'нужно', 'надо', 'менеджер', 'менеджера'
    ]
    
    # Ключевые слова для анализа
    analysis_keywords = [
        'анализ', 'проанализируй', 'статистика', 'данные',
        'продажи', 'выручка', 'прибыль', 'показатели'
    ]
    
    # Ключевые слова для отчетов
    report_keywords = [
        'отчет', 'отчёт', 'неделя', 'месяц', 'период', 'сводка за',
        'итоги за', 'результаты за', 'статистика за'
    ]
    
    # Ключевые слова для инсайтов
    insights_keywords = [
        'инсайты', 'быстро', 'кратко', 'сводка', 'итоги'
    ]
    
    # Ключевые слова для обновления зарплат
    update_keywords = [
        'обновить зарплаты', 'зарплата', 'бонус', 'расчет', 'пересчитать'
    ]
    
    # Ключевые слова для личных расходов
    personal_expense_keywords = [
        'потратил', 'купил', 'заплатил', 'потратила', 'купила', 'заплатила',
        'еда', 'кафе', 'ресторан', 'продукты', 'транспорт', 'такси', 'бензин',
        'развлечения', 'кино', 'игры', 'одежда', 'здоровье', 'лекарства',
        'личный расход', 'личные расходы'
    ]
    
    # Ключевые слова для офисных расходов
    office_expense_keywords = [
        'канцелярия', 'ручки', 'бумага', 'принтер', 'компьютер', 'интернет',
        'связь', 'уборка', 'клининг', 'ремонт', 'аренда офиса', 'офисный расход',
        'офисные расходы', 'офис'
    ]
    
    # Ключевые слова для установки плана
    plan_keywords = [
        'план', 'планирую', 'установить план', 'поставить план', 'план на',
        'январь', 'февраль', 'март', 'апрель', 'май', 'июнь', 'июль', 'август',
        'сентябрь', 'октябрь', 'ноябрь', 'декабрь', 'млн', 'тысяч', 'к'
    ]
    
    
    
    # Проверяем намерение на редактирование
    edit_matches = sum(1 for keyword in edit_keywords if keyword in message_text_lower)
    analysis_matches = sum(1 for keyword in analysis_keywords if keyword in message_text_lower)
    report_matches = sum(1 for keyword in report_keywords if keyword in message_text_lower)
    insights_matches = sum(1 for keyword in insights_keywords if keyword in message_text_lower)
    update_matches = sum(1 for keyword in update_keywords if keyword in message_text_lower)
    personal_expense_matches = sum(1 for keyword in personal_expense_keywords if keyword in message_text_lower)
    office_expense_matches = sum(1 for keyword in office_expense_keywords if keyword in message_text_lower)
    plan_matches = sum(1 for keyword in plan_keywords if keyword in message_text_lower)
    
    # Проверяем, не является ли это нажатием кнопки меню
    if message_text in ["👤 Личные расходы", "🏢 Офисные расходы", "📊 Продажи", "💰 Зарплаты"]:
        # Это нажатие кнопки меню, обрабатываем через button_callback_handler
        if message_text == "👤 Личные расходы":
            await update.message.reply_text("🏠 **ЛИЧНЫЕ РАСХОДЫ**\n\nВыберите действие:", reply_markup=get_personal_expenses_menu_keyboard())
        elif message_text == "🏢 Офисные расходы":
            await update.message.reply_text("🏢 **ОФИСНЫЕ РАСХОДЫ**\n\nВыберите действие:", reply_markup=get_office_expenses_menu_keyboard())
        elif message_text == "📊 Продажи":
            # Сразу показываем таблицу продаж
            await command_handler.analyze_command(update, context)
        elif message_text == "💰 Зарплаты":
            await update.message.reply_text("💰 **ЗАРПЛАТЫ**\n\nВыберите действие:", reply_markup=get_salary_menu_keyboard())
        return
    
    # Определяем наиболее вероятное намерение
    if edit_matches >= 2:  # Если есть минимум 2 ключевых слова для редактирования
        await update.message.reply_text("🤖 Понял, что вы хотите что-то изменить. Обрабатываю...")
        
        # Имитируем context.args для edit_handler
        context.args = update.message.text.split()
        await command_handler.edit_command(update, context)
        
        
    elif report_matches >= 1:
        await update.message.reply_text("📊 Понял, что вы хотите отчет. Генерирую...")
        # TODO: Реализовать генерацию отчетов
        
    elif analysis_matches >= 1:
        await update.message.reply_text("🤖 Понял, что вы хотите анализ. Запускаю...")
        await command_handler.analyze_command(update, context)
        
    elif insights_matches >= 1:
        await update.message.reply_text("🤖 Понял, что вы хотите инсайты. Получаю...")
        await command_handler.insights_command(update, context)
        
    elif update_matches >= 1:
        await update.message.reply_text("🤖 Понял, что нужно обновить зарплаты. Выполняю...")
        await command_handler.update_salary_command(update, context)
        
    elif personal_expense_matches >= 1:
        await update.message.reply_text("🏠 Понял, что вы хотите добавить личный расход. Обрабатываю...")
        if EXPENSES_AVAILABLE:
            success, message = personal_expense_manager.add_expense_from_voice(message_text)
            await update.message.reply_text(f"🏠 {message}")
        else:
            await update.message.reply_text("❌ Менеджер личных расходов недоступен")
        
    elif office_expense_matches >= 1:
        await update.message.reply_text("🏢 Понял, что вы хотите добавить офисный расход. Обрабатываю...")
        if EXPENSES_AVAILABLE:
            success, message = office_expense_manager.add_expense_from_voice(message_text)
            await update.message.reply_text(f"🏢 {message}")
        else:
            await update.message.reply_text("❌ Менеджер офисных расходов недоступен")
        
    else:
        # Если намерение неясно, используем универсальный обработчик
        if CHATGPT_AVAILABLE and len(update.message.text.split()) >= 3:
            # Если сообщение достаточно длинное и ChatGPT доступен - пробуем универсальный запрос
            await update.message.reply_text("🤔 Попробую разобраться в вашем запросе...")
            await command_handler.ask_command(update, context)
        else:
            # Иначе показываем справку
            await update.message.reply_text(
                f"🤖 Получил сообщение: \"{update.message.text}\"\n\n"
                f"💡 **НОВОЕ**: Теперь я понимаю любые вопросы о данных!\n\n"
                f"Примеры того, что я могу:\n"
                f"• \"Сколько заказов у менеджера Иван?\"\n"
                f"• \"Какой товар самый популярный?\"\n"
                f"• \"Покажи заказы больше 100000 тенге\"\n"
                f"• \"Средняя сумма продаж за неделю\"\n"
                f"• \"Сравни продажи разных менеджеров\"\n\n"
                f"📋 Или используйте команды:\n"
                f"📝 /edit - редактировать данные\n"
                f"📊 /analyze - полный анализ\n"
                f"⚡ /insights - быстрая сводка\n"
                f"🔄 /refresh - обновить данные\n"
                f"❓ /help - подробная справка"
            )

async def handle_reply_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик для закрепленных кнопок"""
    message_text = update.message.text
    
    if message_text == "📊 Продажи":
        await update.message.reply_text(
            "📊 **ПРОДАЖИ**\n\n"
            "Выберите действие:",
            reply_markup=get_sales_menu_keyboard()
        )
    
    elif message_text == "💰 Зарплаты":
        await update.message.reply_text(
            "💰 **ЗАРПЛАТЫ**\n\n"
            "Выберите действие:",
            reply_markup=get_salary_menu_keyboard()
        )
    
    elif message_text == "🏠 Личные расходы":
        await update.message.reply_text(
            "🏠 **ЛИЧНЫЕ РАСХОДЫ**\n\n"
            "Выберите действие:",
            reply_markup=get_personal_expenses_menu_keyboard()
        )
    
    elif message_text == "🏢 Офисные расходы":
        await update.message.reply_text(
            "🏢 **ОФИСНЫЕ РАСХОДЫ**\n\n"
            "Выберите действие:",
            reply_markup=get_office_expenses_menu_keyboard()
        )
    
    
    elif message_text == "📈 Полный анализ":
        await update.message.reply_text("🤖 Запускаю полный AI анализ данных...")
        await command_handler.analyze_command(update, context)
    
    elif message_text == "✏️ Редактировать данные":
        await update.message.reply_text(
            "✏️ **РЕДАКТИРОВАНИЕ ДАННЫХ**\n\n"
            "Напишите что нужно изменить, например:\n"
            "• \"В заказе №2 изменить количество котлов с 2 на 1\"\n"
            "• \"Поменять менеджера в заказе №5 на Айдану\"\n"
            "• \"Обновить цену в заказе №1 на 50000\"\n\n"
            "Или используйте команду /edit"
        )
    
    elif message_text == "🔄 Обновить данные":
        await command_handler.refresh_command(update, context)
    
    elif message_text == "❓ Помощь":
        await command_handler.help_command(update, context)
    
    elif message_text == "📋 Главное меню":
        await command_handler.start_command(update, context)
    
    else:
        # Если это не кнопка, обрабатываем как обычное сообщение
        # Продолжаем выполнение функции smart_message_handler
        pass

async def hide_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Скрывает закрепленную клавиатуру"""
    await update.message.reply_text(
        "⌨️ Клавиатура скрыта. Используйте команды или /start для возврата.",
        reply_markup=ReplyKeyboardMarkup([], resize_keyboard=True, one_time_keyboard=True)
    )

async def show_keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показывает закрепленную клавиатуру"""
    await update.message.reply_text(
        "⌨️ Клавиатура активирована!",
        reply_markup=get_main_reply_keyboard()
    )

def main():
    from config import LOGGING_CONFIG, BOT_SETTINGS, FILE_PATHS
    
    # Настройка подробного логирования
    logging.basicConfig(
        format=LOGGING_CONFIG['format'],
        level=getattr(logging, LOGGING_CONFIG['level']),
        handlers=[
            logging.StreamHandler(),  # Вывод в терминал
            logging.FileHandler(FILE_PATHS['log_file'], encoding='utf-8')  # Запись в файл
        ]
    )
    
    # Включаем подробное логирование для telegram
    logging.getLogger("telegram").setLevel(logging.INFO)
    logging.getLogger("httpx").setLevel(logging.INFO)
    
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", command_handler.start_command))
    app.add_handler(CommandHandler("update", command_handler.update_salary_command))
    app.add_handler(CommandHandler("analyze", command_handler.analyze_command))
    app.add_handler(CommandHandler("insights", command_handler.insights_command))
    app.add_handler(CommandHandler("edit", command_handler.edit_command))
    app.add_handler(CommandHandler("refresh", command_handler.refresh_command))
    app.add_handler(CommandHandler("ask", command_handler.ask_command))
    app.add_handler(CommandHandler("help", command_handler.help_command))
    app.add_handler(CommandHandler("hide", hide_keyboard_handler))
    app.add_handler(CommandHandler("show", show_keyboard_handler))
    
    # Добавляем обработчик callback запросов (вкладки)
    app.add_handler(CallbackQueryHandler(button_callback_handler))
    
    # Добавляем обработчик голосовых сообщений
    app.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    
    # Добавляем умный обработчик обычных сообщений (включает обработку кнопок)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_message_handler))

    chatgpt_status = "✅ ChatGPT AI доступен" if CHATGPT_AVAILABLE else "⚠️ ChatGPT AI недоступен"
    voice_status = "✅ Голосовые команды доступны" if VOICE_AVAILABLE else "⚠️ Голосовые команды недоступны"
    print(f"🤖 Бот запущен")
    print(f"📊 {chatgpt_status}")
    print(f"🎤 {voice_status}")
    print(f"📁 Excel файл: {FILE_PATHS['excel_file']}")
    print(f"📝 Логирование включено - все диалоги записываются в терминал и {FILE_PATHS['log_file']}")
    
    # Настройки polling
    app.run_polling(
        drop_pending_updates=True,
        **BOT_SETTINGS
    )

if __name__ == "__main__":
    main()