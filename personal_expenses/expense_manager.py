"""
Менеджер личных расходов
"""
import sys
import os
from typing import List, Dict, Any

# Добавляем путь к родительской директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_expense_manager import BaseExpenseManager


class PersonalExpenseManager(BaseExpenseManager):
    """Менеджер личных расходов"""
    
    def __init__(self, excel_file_path: str):
        # Постоянные личные расходы
        fixed_personal_expenses = [
            {"category": "жилье", "amount": 250000, "payment_method": "карта", "comments": "аренда квартиры"},
            {"category": "коммунальные услуги", "amount": 14000, "payment_method": "карта", "comments": ""},
            {"category": "сотовая связь", "amount": 25000, "payment_method": "карта", "comments": ""},
            {"category": "интернет", "amount": 25000, "payment_method": "карта", "comments": "казахтелеком"}
        ]
        
        super().__init__(excel_file_path, 'personal', fixed_personal_expenses)
    
    def _create_categorization_prompt(self, text: str) -> str:
        """Создает промпт для категоризации личных расходов"""
        return f"""
        Проанализируй следующий текст о расходе и определи категорию из списка:
        
        Доступные категории:
        - кафе (кафе, ресторан, бао, вau, starbucks, кофейня, бар, пиццерия, суши, фастфуд, рестораны)
        - еда (продукты, завтрак, обед, ужин, продукты в магазине, доставка еды)
        - жилье (аренда, коммунальные услуги, интернет, сотовая связь)
        - транспорт (такси, бензин, общественный транспорт)
        - развлечения (кино, игры, подписки)
        - здоровье (лекарства, врачи, спорт)
        - одежда (покупка одежды, обуви)
        - Дом и быт(мебель, техника / гаджеты, ремонт)
        - Образование и развитие(курсы, книги, тренинги, семинары)
        - Путешествия (билеты, отель, поездка, тур)
        - Финансовые обязательства (кредиты, займы, кредитные карты)
        - прочее (все остальное)
        
        Текст: "{text}"
        
        Верни только название категории в формате JSON:
        {{"category": "название_категории", "confidence": 0.95}}
        """
    
    def _create_analysis_prompt(self, category_summary, total_amount: float) -> str:
        """Создает промпт для анализа личных расходов"""
        return f"""
        Проанализируй мои личные расходы за последние 30 дней и дай рекомендации:
        
        Общая сумма: {total_amount:,.0f} тенге
        
        Расходы по категориям:
        {chr(10).join([f"- {cat}: {amount:,.0f} тенге ({amount/total_amount*100:.1f}%)" for cat, amount in category_summary.items()])}
        
        Дай краткий анализ (2-3 предложения) и 3 практических совета по экономии.
        """
    
