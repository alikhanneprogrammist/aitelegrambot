"""
Модуль для обработки сообщений бота
"""
import os
import logging
from typing import Dict, Any
from telegram import Update
from telegram.ext import ContextTypes
from sales_folder.chatgpt_analyzer import ChatGPTAnalyzer
from personal_expenses.expense_manager import PersonalExpenseManager
from office_expenses.expense_manager import OfficeExpenseManager
from utils import data_cache
from config import TELEGRAM_SETTINGS, INTENT_KEYWORDS

logger = logging.getLogger(__name__)


class MessageHandler:
    """
    Класс для обработки различных типов сообщений
    
    Обрабатывает текстовые и голосовые сообщения пользователей,
    определяет намерения и направляет к соответствующим обработчикам.
    """
    
    def __init__(self, chatgpt_analyzer: ChatGPTAnalyzer, 
                 personal_expense_manager: PersonalExpenseManager,
                 office_expense_manager: OfficeExpenseManager):
        self.chatgpt_analyzer = chatgpt_analyzer
        self.personal_expense_manager = personal_expense_manager
        self.office_expense_manager = office_expense_manager
    
    async def handle_voice_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик голосовых сообщений"""
        # TODO: Реализовать обработку голосовых сообщений
        await update.message.reply_text("🎤 Голосовые сообщения временно недоступны")
    
    async def handle_text_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обработчик текстовых сообщений"""
        message_text = update.message.text
        message_text_lower = message_text.lower()
        
        # Определяем намерение пользователя
        intent = self._detect_intent(message_text_lower)
        
        if intent == 'edit':
            await self._handle_edit_request(update, context)
        elif intent == 'analysis':
            await self._handle_analysis_request(update, context)
        elif intent == 'insights':
            await self._handle_insights_request(update, context)
        elif intent == 'update':
            await self._handle_update_request(update, context)
        elif intent == 'personal_expense':
            await self._handle_personal_expense_request(update, context)
        elif intent == 'office_expense':
            await self._handle_office_expense_request(update, context)
        else:
            await self._handle_unknown_request(update, context)
    
    def _detect_intent(self, message_text: str) -> str:
        """Определяет намерение пользователя на основе ключевых слов"""
        # Ключевые слова для редактирования
        edit_matches = sum(1 for keyword in INTENT_KEYWORDS['edit'] if keyword in message_text)
        
        # Ключевые слова для анализа
        analysis_matches = sum(1 for keyword in INTENT_KEYWORDS['analysis'] if keyword in message_text)
        
        # Ключевые слова для инсайтов
        insights_matches = sum(1 for keyword in INTENT_KEYWORDS['insights'] if keyword in message_text)
        
        # Ключевые слова для обновления
        update_matches = sum(1 for keyword in INTENT_KEYWORDS['update'] if keyword in message_text)
        
        # Ключевые слова для личных расходов
        personal_expense_keywords = [
            'потратил', 'купил', 'заплатил', 'потратила', 'купила', 'заплатила',
            'еда', 'кафе', 'ресторан', 'продукты', 'транспорт', 'такси', 'бензин',
            'развлечения', 'кино', 'игры', 'одежда', 'здоровье', 'лекарства',
            'личный расход', 'личные расходы'
        ]
        personal_expense_matches = sum(1 for keyword in personal_expense_keywords if keyword in message_text)
        
        # Ключевые слова для офисных расходов
        office_expense_keywords = [
            'канцелярия', 'ручки', 'бумага', 'принтер', 'компьютер', 'интернет',
            'связь', 'уборка', 'клининг', 'ремонт', 'аренда офиса', 'офисный расход',
            'офисные расходы', 'офис'
        ]
        office_expense_matches = sum(1 for keyword in office_expense_keywords if keyword in message_text)
        
        # Определяем наиболее вероятное намерение
        if edit_matches >= 2:
            return 'edit'
        elif personal_expense_matches >= 1:
            return 'personal_expense'
        elif office_expense_matches >= 1:
            return 'office_expense'
        elif analysis_matches >= 1:
            return 'analysis'
        elif insights_matches >= 1:
            return 'insights'
        elif update_matches >= 1:
            return 'update'
        else:
            return 'unknown'
    
    async def _handle_edit_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает запросы на редактирование"""
        await update.message.reply_text("🤖 Понял, что вы хотите что-то изменить. Обрабатываю...")
        # TODO: Реализовать логику редактирования
    
    async def _handle_analysis_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает запросы на анализ"""
        await update.message.reply_text("🤖 Понял, что вы хотите анализ. Запускаю...")
        # TODO: Реализовать логику анализа
    
    async def _handle_insights_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает запросы на инсайты"""
        await update.message.reply_text("🤖 Понял, что вы хотите инсайты. Получаю...")
        # TODO: Реализовать логику инсайтов
    
    async def _handle_update_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает запросы на обновление"""
        await update.message.reply_text("🤖 Понял, что нужно обновить зарплаты. Выполняю...")
        # TODO: Реализовать логику обновления
    
    async def _handle_personal_expense_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает запросы на добавление личных расходов"""
        await update.message.reply_text("🏠 Понял, что вы хотите добавить личный расход. Обрабатываю...")
        # TODO: Реализовать логику добавления личных расходов
    
    async def _handle_office_expense_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает запросы на добавление офисных расходов"""
        await update.message.reply_text("🏢 Понял, что вы хотите добавить офисный расход. Обрабатываю...")
        # TODO: Реализовать логику добавления офисных расходов
    
    async def _handle_unknown_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Обрабатывает неизвестные запросы"""
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
