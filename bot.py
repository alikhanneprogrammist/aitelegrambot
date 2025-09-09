import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from salary_update import update_salary
from gemini_analyzer import GeminiAnalyzer
from voice_handler import VoiceHandler
from dotenv import load_dotenv
from utils import data_cache

# Загружаем переменные окружения
load_dotenv()

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
EXCEL_FILE = os.getenv("EXCEL_FILE_NAME", "Alseit.xlsx")

# Инициализируем Gemini анализатор
try:
    gemini_analyzer = GeminiAnalyzer()
    GEMINI_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Gemini недоступен: {e}")
    GEMINI_AVAILABLE = False

# Инициализируем обработчик голосовых сообщений
try:
    voice_handler = VoiceHandler()
    VOICE_AVAILABLE = True
except Exception as e:
    print(f"⚠️ Голосовой обработчик недоступен: {e}")
    VOICE_AVAILABLE = False


# Команда /update запускает salary_update.py
async def update_salary_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        result = update_salary()
        await update.message.reply_text(result)
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {e}")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gemini_status = "✅ Доступен" if GEMINI_AVAILABLE else "❌ Недоступен"
    voice_status = "✅ Доступен" if VOICE_AVAILABLE else "❌ Недоступен"
    await update.message.reply_text(
        f"🤖 Привет! Я умный финансовый бот с AI анализом.\n\n"
        f"📊 Gemini AI: {gemini_status}\n"
        f"🎤 Голосовые команды: {voice_status}\n\n"
        f"🧠 **НОВАЯ ФУНКЦИЯ**: Теперь я понимаю ЛЮБЫЕ вопросы о данных!\n"
        f"Просто напишите что хотите узнать:\n"
        f"• \"Сколько заказов у менеджера Иван?\"\n"
        f"• \"Какой товар самый популярный?\"\n"
        f"• \"Покажи заказы больше 100000 тенге\"\n"
        f"• \"Изменить в заказе номер 2 количество на 3\"\n"
        f"• \"Отчет за эту неделю\"\n\n"
        f"🎤 **ГОЛОСОВЫЕ КОМАНДЫ**: Теперь вы можете говорить!\n"
        f"Примеры голосовых команд:\n"
        f"• \"Измени количество котлов 3 штуки в номере заказа 2\"\n"
        f"• \"Поменяй цену в заказе 5 на 50000\"\n"
        f"• \"Назначь менеджером Иван в заказе 3\"\n\n"
        f"📋 Команды (если нужны):\n"
        f"• /update - обновить зарплаты\n"
        f"• /analyze - полный AI анализ данных\n"
        f"• /insights - быстрые инсайты\n"
        f"• /edit - редактировать Excel через AI\n"
        f"• /refresh - обновить данные из Excel\n"
        f"• /ask - быстрый вопрос о данных\n"
        f"• /help - помощь"
    )

async def analyze_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Полный AI анализ данных"""
    if not GEMINI_AVAILABLE:
        await update.message.reply_text("❌ Gemini AI недоступен. Проверьте настройки API ключа.")
        return
    
    await update.message.reply_text("🔄 Анализирую данные... Это может занять несколько секунд.")
    
    try:
        # Получаем полный путь к файлу
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        analysis = gemini_analyzer.analyze_sales_data(excel_path)
        
        # Разбиваем длинный ответ на части (Telegram имеет лимит на длину сообщения)
        if len(analysis) > 4000:
            # Отправляем по частям
            parts = [analysis[i:i+4000] for i in range(0, len(analysis), 4000)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"📈 Анализ (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await update.message.reply_text(f"📈 AI Анализ данных:\n\n{analysis}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при анализе: {str(e)}")

async def insights_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрые инсайты по данным"""
    try:
        # Получаем полный путь к файлу
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        insights = gemini_analyzer.get_quick_insights(excel_path)
        await update.message.reply_text(insights)
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при получении инсайтов: {str(e)}")

async def edit_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирование данных в Excel файле"""
    if not GEMINI_AVAILABLE:
        await update.message.reply_text("❌ Gemini AI недоступен. Проверьте настройки API ключа.")
        return
    
    # Получаем текст сообщения (запрос на изменение)
    if not context.args:
        await update.message.reply_text(
            "📝 Укажите, что нужно изменить.\n\n"
            "Примеры:\n"
            "• /edit заказ номер #2 вместо двух котлов взял один\n"
            "• /edit изменить количество товара 'котлы' в заказе 5 с 3 на 1\n"
            "• /edit обновить цену товара в заказе 1 на 50000\n"
            "• /edit назначить менеджером Иван в заказе 3"
        )
        return
    
    edit_request = " ".join(context.args)
    await update.message.reply_text("🔄 Обрабатываю запрос на изменение...")
    
    try:
        # Получаем полный путь к файлу
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        result = gemini_analyzer.edit_excel_data(excel_path, edit_request)
        
        # Разбиваем длинный ответ на части
        if len(result) > 4000:
            parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"📝 Результат (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await update.message.reply_text(f"📝 {result}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при редактировании: {str(e)}")

async def refresh_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обновление данных из Excel файла"""
    try:
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        
        # Проверяем существование файла
        if not os.path.exists(excel_path):
            await update.message.reply_text("❌ Excel файл не найден!")
            return
        
        # Получаем информацию о кэше до очистки
        cache_info_before = data_cache.get_cache_info()
        
        # Очищаем кэш для файла
        data_cache.refresh_file(excel_path)
        
        # Получаем информацию о файле
        file_mod_time = os.path.getmtime(excel_path)
        file_size = os.path.getsize(excel_path)
        
        await update.message.reply_text(
            f"✅ Данные обновлены!\n\n"
            f"📁 Файл: {EXCEL_FILE}\n"
            f"📅 Изменен: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(file_mod_time))}\n"
            f"📊 Размер: {file_size:,} байт\n"
            f"🗑️ Очищено из кэша: {cache_info_before['cache_size']} записей\n\n"
            f"Теперь бот будет использовать актуальные данные из Excel файла."
        )
        
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обновлении данных: {str(e)}")

async def generate_report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Генерация отчетов по периодам"""
    if not GEMINI_AVAILABLE:
        await update.message.reply_text("❌ Gemini AI недоступен. Проверьте настройки API ключа.")
        return
    
    try:
        # Получаем полный путь к файлу
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        result = gemini_analyzer.generate_period_report(excel_path, update.message.text)
        
        # Разбиваем длинный ответ на части
        if len(result) > 4000:
            parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"📊 Отчет (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await update.message.reply_text(f"📊 {result}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при генерации отчета: {str(e)}")

async def universal_query_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Универсальный обработчик любых запросов по данным"""
    if not GEMINI_AVAILABLE:
        await update.message.reply_text("❌ Gemini AI недоступен. Проверьте настройки API ключа.")
        return
    
    try:
        # Получаем полный путь к файлу
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        result = gemini_analyzer.universal_query(excel_path, update.message.text)
        
        # Разбиваем длинный ответ на части
        if len(result) > 4000:
            parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"🤖 Ответ (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await update.message.reply_text(f"🤖 {result}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка при обработке запроса: {str(e)}")

async def ask_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Быстрые вопросы о данных"""
    if not GEMINI_AVAILABLE:
        await update.message.reply_text("❌ Gemini AI недоступен. Проверьте настройки API ключа.")
        return
    
    # Получаем вопрос
    if not context.args:
        await update.message.reply_text(
            "❓ Задайте вопрос о данных.\n\n"
            "Примеры:\n"
            "• /ask средний чек за неделю\n"
            "• /ask сколько заказов у Ивана\n"
        )
        return
    
    question = " ".join(context.args)
    await update.message.reply_text("🤔 Анализирую...")
    
    try:
        excel_path = os.path.join(os.path.dirname(__file__), EXCEL_FILE)
        result = gemini_analyzer.universal_query(excel_path, question)
        
        # Ответ должен быть коротким, но все равно проверим длину
        if len(result) > 4000:
            parts = [result[i:i+4000] for i in range(0, len(result), 4000)]
            for i, part in enumerate(parts):
                await update.message.reply_text(f"💡 Ответ (часть {i+1}/{len(parts)}):\n\n{part}")
        else:
            await update.message.reply_text(f"💡 {result}")
            
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")

async def voice_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик голосовых сообщений"""
    if not VOICE_AVAILABLE:
        await update.message.reply_text("❌ Голосовые команды недоступны. Проверьте установку зависимостей.")
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
            await edit_handler(update, context)
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
            
            await universal_query_handler(mock_update, context)
            
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

🤖 ПРИМЕРЫ УМНЫХ ЗАПРОСОВ:
• "Сколько заказов у менеджера Анна?"
• "Какой товар приносит больше всего прибыли?"
• "Покажи все заказы клиента ТОО Строй"
• "Средняя сумма продаж в январе"
• "Сравни эффективность менеджеров"
• "Найди самые дорогие заказы"
• "Статистика по дням недели"

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
    """Умный обработчик сообщений - автоматически определяет намерения пользователя"""
    message_text = update.message.text.lower()
    
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
    
    # Проверяем намерение на редактирование
    edit_matches = sum(1 for keyword in edit_keywords if keyword in message_text)
    analysis_matches = sum(1 for keyword in analysis_keywords if keyword in message_text)
    report_matches = sum(1 for keyword in report_keywords if keyword in message_text)
    insights_matches = sum(1 for keyword in insights_keywords if keyword in message_text)
    update_matches = sum(1 for keyword in update_keywords if keyword in message_text)
    
    # Определяем наиболее вероятное намерение
    if edit_matches >= 2:  # Если есть минимум 2 ключевых слова для редактирования
        await update.message.reply_text("🤖 Понял, что вы хотите что-то изменить. Обрабатываю...")
        
        # Имитируем context.args для edit_handler
        context.args = update.message.text.split()
        await edit_handler(update, context)
        
    elif report_matches >= 1:
        await update.message.reply_text("📊 Понял, что вы хотите отчет. Генерирую...")
        await generate_report_handler(update, context)
        
    elif analysis_matches >= 1:
        await update.message.reply_text("🤖 Понял, что вы хотите анализ. Запускаю...")
        await analyze_handler(update, context)
        
    elif insights_matches >= 1:
        await update.message.reply_text("🤖 Понял, что вы хотите инсайты. Получаю...")
        await insights_handler(update, context)
        
    elif update_matches >= 1:
        await update.message.reply_text("🤖 Понял, что нужно обновить зарплаты. Выполняю...")
        await update_salary_handler(update, context)
        
    else:
        # Если намерение неясно, используем универсальный обработчик
        if GEMINI_AVAILABLE and len(update.message.text.split()) >= 3:
            # Если сообщение достаточно длинное и Gemini доступен - пробуем универсальный запрос
            await update.message.reply_text("🤔 Попробую разобраться в вашем запросе...")
            await universal_query_handler(update, context)
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

def main():
    app = Application.builder().token(TOKEN).build()
    
    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("update", update_salary_handler))
    app.add_handler(CommandHandler("analyze", analyze_handler))
    app.add_handler(CommandHandler("insights", insights_handler))
    app.add_handler(CommandHandler("edit", edit_handler))
    app.add_handler(CommandHandler("refresh", refresh_handler))
    app.add_handler(CommandHandler("ask", ask_handler))
    app.add_handler(CommandHandler("help", help_handler))
    
    # Добавляем обработчик голосовых сообщений
    app.add_handler(MessageHandler(filters.VOICE, voice_message_handler))
    
    # Добавляем умный обработчик обычных сообщений (должен быть последним!)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, smart_message_handler))

    gemini_status = "✅ Gemini AI доступен" if GEMINI_AVAILABLE else "⚠️ Gemini AI недоступен"
    voice_status = "✅ Голосовые команды доступны" if VOICE_AVAILABLE else "⚠️ Голосовые команды недоступны"
    print(f"🤖 Бот запущен")
    print(f"📊 {gemini_status}")
    print(f"🎤 {voice_status}")
    print(f"📁 Excel файл: {EXCEL_FILE}")
    
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()