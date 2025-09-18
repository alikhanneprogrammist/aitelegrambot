"""
Модуль для обработки команд бота
"""
import os
import logging
from typing import Optional
from telegram import Update
from telegram.ext import ContextTypes
from sales_folder.chatgpt_analyzer import ChatGPTAnalyzer
from salary_folder.salary_update import update_salary, get_salary_summary
from utils import data_cache, get_gross_profit, get_net_profit, get_net_profit_from_sales, get_office_expenses_total, get_office_summary, add_office_constants
from config import FILE_PATHS, TELEGRAM_SETTINGS

logger = logging.getLogger(__name__)


class CommandHandler:
    """
    Класс для обработки команд бота
    
    Содержит методы для обработки всех команд бота,
    включая анализ данных, редактирование, обновление и справку.
    """
    
    def __init__(self, chatgpt_analyzer: ChatGPTAnalyzer):
        self.chatgpt_analyzer = chatgpt_analyzer
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /start"""
        chatgpt_status = "✅ Доступен" if self.chatgpt_analyzer else "❌ Недоступен"
        
        welcome_text = (
            f"🤖 **Добро пожаловать!**\n\n"
            f"Я умный финансовый бот с AI анализом для управления бизнесом.\n\n"
            f"📊 **ChatGPT AI:** {chatgpt_status}\n\n"
            f"🚀 **БЫСТРЫЕ КОМАНДЫ:**\n"
            f"• `/update` - обновить зарплаты и бонусы\n"
            f"• `/analyze` - полный AI анализ данных\n"
            f"• `/insights` - быстрые инсайты по продажам\n"
            f"• `/edit` - редактировать данные через AI\n"
            f"• `/help` - справка по всем командам\n\n"
            f"💡 **Используйте кнопки ниже** для быстрого доступа к функциям!"
        )
        
        await update.message.reply_text(welcome_text)
    
    async def update_salary_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /update"""
        try:
            result = update_salary()
            await update.message.reply_text(result, parse_mode=None)
        except Exception as e:
            logger.error(f"Ошибка обновления зарплат: {e}")
            await update.message.reply_text(f"Ошибка: {e}")
    
    async def analyze_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /analyze"""
        if not self.chatgpt_analyzer:
            await update.message.reply_text("❌ ChatGPT AI недоступен. Проверьте настройки API ключа.")
            return
        
        await update.message.reply_text("🔄 Анализирую данные... Это может занять несколько секунд.")
        
        try:
            excel_path = os.path.join(os.path.dirname(__file__), FILE_PATHS['excel_file'])
            analysis = self.chatgpt_analyzer.analyze_sales_data(excel_path)
            
            # Разбиваем длинный ответ на части
            if len(analysis) > TELEGRAM_SETTINGS['max_message_length']:
                parts = self._split_message(analysis, TELEGRAM_SETTINGS['max_message_length'])
                for i, part in enumerate(parts):
                    await update.message.reply_text(f"📈 Анализ (часть {i+1}/{len(parts)}):\n\n{part}")
            else:
                await update.message.reply_text(f"📈 AI Анализ данных:\n\n{analysis}")
                
        except Exception as e:
            logger.error(f"Ошибка при анализе: {e}")
            await update.message.reply_text(f"❌ Ошибка при анализе: {str(e)}")
    
    async def insights_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /insights"""
        try:
            excel_path = os.path.join(os.path.dirname(__file__), FILE_PATHS['excel_file'])
            insights = self.chatgpt_analyzer.get_quick_insights(excel_path)
            await update.message.reply_text(insights)
        except Exception as e:
            logger.error(f"Ошибка при получении инсайтов: {e}")
            await update.message.reply_text(f"❌ Ошибка при получении инсайтов: {str(e)}")
    
    async def edit_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /edit"""
        if not self.chatgpt_analyzer:
            await update.message.reply_text("❌ ChatGPT AI недоступен. Проверьте настройки API ключа.")
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
            excel_path = os.path.join(os.path.dirname(__file__), FILE_PATHS['excel_file'])
            result = self.chatgpt_analyzer.edit_excel_data(excel_path, edit_request)
            
            # Разбиваем длинный ответ на части
            if len(result) > TELEGRAM_SETTINGS['max_message_length']:
                parts = self._split_message(result, TELEGRAM_SETTINGS['max_message_length'])
                for i, part in enumerate(parts):
                    await update.message.reply_text(f"📝 Результат (часть {i+1}/{len(parts)}):\n\n{part}")
            else:
                await update.message.reply_text(f"📝 {result}")
                
        except Exception as e:
            logger.error(f"Ошибка при редактировании: {e}")
            await update.message.reply_text(f"❌ Ошибка при редактировании: {str(e)}")
    
    async def refresh_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /refresh"""
        try:
            excel_path = os.path.join(os.path.dirname(__file__), FILE_PATHS['excel_file'])
            
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
                f"📁 Файл: {FILE_PATHS['excel_file']}\n"
                f"📅 Изменен: {file_mod_time}\n"
                f"📊 Размер: {file_size:,} байт\n"
                f"🗑️ Очищено из кэша: {cache_info_before['cache_size']} записей\n\n"
                f"Теперь бот будет использовать актуальные данные из Excel файла."
            )
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных: {e}")
            await update.message.reply_text(f"❌ Ошибка при обновлении данных: {str(e)}")
    
    async def ask_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /ask"""
        if not self.chatgpt_analyzer:
            await update.message.reply_text("❌ ChatGPT AI недоступен. Проверьте настройки API ключа.")
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
            excel_path = os.path.join(os.path.dirname(__file__), FILE_PATHS['excel_file'])
            result = self.chatgpt_analyzer.universal_query(excel_path, question)
            
            # Ответ должен быть коротким, но все равно проверим длину
            if len(result) > TELEGRAM_SETTINGS['max_message_length']:
                parts = self._split_message(result, TELEGRAM_SETTINGS['max_message_length'])
                for i, part in enumerate(parts):
                    await update.message.reply_text(f"💡 Ответ (часть {i+1}/{len(parts)}):\n\n{part}")
            else:
                await update.message.reply_text(f"💡 {result}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке запроса: {e}")
            await update.message.reply_text(f"❌ Ошибка: {str(e)}")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик команды /help"""
        help_text = """
🤖 ФИНАНСОВЫЙ БОТ - СПРАВКА

📊 ОСНОВНЫЕ КОМАНДЫ:
• /start - начать работу с ботом
• /update - обновить зарплаты и рассчитать бонусы
• /analyze - полный AI анализ данных (ChatGPT)
• /insights - быстрые инсайты по продажам
• /edit - редактировать данные в Excel (AI)
• /refresh - обновить данные из Excel
• /ask - быстрый вопрос о данных
• /help - эта справка

🔧 НАСТРОЙКИ:
• Убедитесь, что файл Alseit.xlsx находится в папке с ботом
• Для AI анализа нужен OPENAI_API_KEY в .env файле

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

📝 ПРИМЕРЫ РЕДАКТИРОВАНИЯ:
• /edit заказ номер #2 вместо двух котлов взял один
• /edit изменить количество товара 'котлы' в заказе 5 с 3 на 1
• /edit обновить цену товара в заказе 1 на 50000
• /edit назначить менеджером Иван в заказе 3
        """
        await update.message.reply_text(help_text)
    
    def _split_message(self, text: str, max_length: int) -> list:
        """Разбивает длинное сообщение на части"""
        if len(text) <= max_length:
            return [text]
        
        parts = []
        for i in range(0, len(text), max_length):
            parts.append(text[i:i + max_length])
        
        return parts
