"""
Тесты для менеджеров расходов
"""
import pytest
import pandas as pd
import tempfile
import os
from unittest.mock import Mock, patch
import sys

# Добавляем путь к родительской директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from base_expense_manager import BaseExpenseManager
from personal_expenses.expense_manager import PersonalExpenseManager
from office_expenses.expense_manager import OfficeExpenseManager


class TestBaseExpenseManager:
    """Тесты для базового менеджера расходов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_file.close()
        
        self.fixed_expenses = [
            {"category": "тест", "amount": 1000, "payment_method": "карта", "comments": "тест"}
        ]
        
        self.manager = BaseExpenseManager(
            self.temp_file.name, 
            'test', 
            self.fixed_expenses
        )
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_init(self):
        """Тест инициализации"""
        assert self.manager.excel_file == self.temp_file.name
        assert self.manager.sheet_name == 'test'
        assert self.manager.fixed_expenses == self.fixed_expenses
    
    def test_extract_amount_from_text(self):
        """Тест извлечения суммы из текста"""
        # Тест с "к" в конце
        assert self.manager._extract_amount_from_text("150к кафе") == 150000
        assert self.manager._extract_amount_from_text("1.5к еда") == 1500
        
        # Тест с обычными числами
        assert self.manager._extract_amount_from_text("5000 продукты") == 5000
        assert self.manager._extract_amount_from_text("15000 транспорт") == 15000
        
        # Тест без суммы
        assert self.manager._extract_amount_from_text("кафе") is None
    
    def test_determine_payment_method(self):
        """Тест определения способа оплаты"""
        assert self.manager._determine_payment_method("потратил 5000 наличными") == "наличные"
        assert self.manager._determine_payment_method("купил наличкой") == "наличные"
        assert self.manager._determine_payment_method("заплатил деньгами") == "наличные"
        assert self.manager._determine_payment_method("потратил 5000") == "карта"
    
    def test_read_excel_data_empty(self):
        """Тест чтения пустого Excel файла"""
        df = self.manager._read_excel_data()
        assert df.empty
        assert list(df.columns) == ['date', 'category', 'amount', 'payment_method', 'comments']
    
    def test_save_excel_data(self):
        """Тест сохранения данных в Excel"""
        test_data = pd.DataFrame({
            'date': ['01.01.2024'],
            'category': ['тест'],
            'amount': [1000],
            'payment_method': ['карта'],
            'comments': ['тест']
        })
        
        self.manager._save_excel_data(test_data)
        
        # Проверяем, что данные сохранились
        saved_data = self.manager._read_excel_data()
        assert not saved_data.empty
        assert saved_data.iloc[0]['category'] == 'тест'
        assert saved_data.iloc[0]['amount'] == 1000


class TestPersonalExpenseManager:
    """Тесты для менеджера личных расходов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_file.close()
        
        self.manager = PersonalExpenseManager(self.temp_file.name)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_init(self):
        """Тест инициализации личного менеджера"""
        assert self.manager.sheet_name == 'personal'
        assert len(self.manager.fixed_expenses) == 4
        assert self.manager.fixed_expenses[0]['category'] == 'жилье'
    
    @patch('base_expense_manager.OpenAI')
    def test_categorize_expense(self, mock_openai):
        """Тест категоризации расходов"""
        # Мокаем ответ от OpenAI
        mock_response = Mock()
        mock_response.choices[0].message.content = '{"category": "еда", "confidence": 0.9}'
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        category, confidence = self.manager.categorize_expense("купил продукты")
        assert category == "еда"
        assert confidence == 0.9
    
    def test_create_categorization_prompt(self):
        """Тест создания промпта для категоризации"""
        prompt = self.manager._create_categorization_prompt("купил хлеб")
        assert "купил хлеб" in prompt
        assert "кафе" in prompt
        assert "еда" in prompt
        assert "жилье" in prompt


class TestOfficeExpenseManager:
    """Тесты для менеджера офисных расходов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_file.close()
        
        self.manager = OfficeExpenseManager(self.temp_file.name)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    def test_init(self):
        """Тест инициализации офисного менеджера"""
        assert self.manager.sheet_name == 'office'
        assert len(self.manager.fixed_expenses) == 4
        assert self.manager.fixed_expenses[0]['category'] == 'аренда офиса'
    
    def test_create_categorization_prompt(self):
        """Тест создания промпта для категоризации"""
        prompt = self.manager._create_categorization_prompt("купил канцелярию")
        assert "купил канцелярию" in prompt
        assert "канцелярия" in prompt
        assert "аренда офиса" in prompt
        assert "коммунальные услуги" in prompt


class TestExpenseManagerIntegration:
    """Интеграционные тесты для менеджеров расходов"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.temp_file = tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False)
        self.temp_file.close()
        
        self.personal_manager = PersonalExpenseManager(self.temp_file.name)
        self.office_manager = OfficeExpenseManager(self.temp_file.name)
    
    def teardown_method(self):
        """Очистка после каждого теста"""
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
    
    @patch('base_expense_manager.OpenAI')
    def test_add_expense_from_voice_personal(self, mock_openai):
        """Тест добавления личного расхода через голос"""
        # Мокаем ответ от OpenAI
        mock_response = Mock()
        mock_response.choices[0].message.content = '{"category": "еда", "confidence": 0.9}'
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        success, message = self.personal_manager.add_expense_from_voice("потратил 5000 на еду")
        
        assert success is True
        assert "еда" in message
        assert "5000" in message
        
        # Проверяем, что данные сохранились
        df = self.personal_manager._read_excel_data()
        assert not df.empty
        assert df.iloc[0]['category'] == 'еда'
        assert df.iloc[0]['amount'] == 5000
    
    @patch('base_expense_manager.OpenAI')
    def test_add_expense_from_voice_office(self, mock_openai):
        """Тест добавления офисного расхода через голос"""
        # Мокаем ответ от OpenAI
        mock_response = Mock()
        mock_response.choices[0].message.content = '{"category": "канцелярия", "confidence": 0.9}'
        mock_openai.return_value.chat.completions.create.return_value = mock_response
        
        success, message = self.office_manager.add_expense_from_voice("купил канцелярию на 3000")
        
        assert success is True
        assert "канцелярия" in message
        assert "3000" in message
        
        # Проверяем, что данные сохранились
        df = self.office_manager._read_excel_data()
        assert not df.empty
        assert df.iloc[0]['category'] == 'канцелярия'
        assert df.iloc[0]['amount'] == 3000
    
    def test_get_monthly_summary_empty(self):
        """Тест получения сводки за месяц для пустых данных"""
        summary = self.personal_manager.get_monthly_summary()
        assert "Нет данных о расходах" in summary
    
    def test_get_recent_expenses_empty(self):
        """Тест получения последних расходов для пустых данных"""
        recent = self.personal_manager.get_recent_expenses()
        assert "Нет данных" in recent
    
    def test_get_weekly_summary_empty(self):
        """Тест получения недельной сводки для пустых данных"""
        weekly = self.personal_manager.get_weekly_summary()
        assert "Нет данных" in weekly


if __name__ == "__main__":
    pytest.main([__file__])

