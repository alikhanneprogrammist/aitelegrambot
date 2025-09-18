"""
Тесты для утилит
"""
import pytest
import pandas as pd
import tempfile
import os
import sys
from unittest.mock import patch, Mock

# Добавляем путь к родительской директории
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils import DataCache, find_column, clean_numeric_data, split_message_if_long


class TestDataCache:
    """Тесты для кэша данных"""
    
    def setup_method(self):
        """Настройка для каждого теста"""
        self.cache = DataCache()
    
    def test_init(self):
        """Тест инициализации кэша"""
        assert self.cache._cache == {}
        assert self.cache._timestamps == {}
        assert self.cache._file_mod_times == {}
    
    def test_get_file_mod_time(self):
        """Тест получения времени модификации файла"""
        # Создаем временный файл
        with tempfile.NamedTemporaryFile(delete=False) as temp_file:
            temp_file.write(b"test")
            temp_file_path = temp_file.name
        
        try:
            mod_time = self.cache._get_file_mod_time(temp_file_path)
            assert isinstance(mod_time, float)
            assert mod_time > 0
        finally:
            os.unlink(temp_file_path)
    
    def test_get_file_mod_time_nonexistent(self):
        """Тест получения времени модификации несуществующего файла"""
        mod_time = self.cache._get_file_mod_time("nonexistent_file.txt")
        assert mod_time == 0.0
    
    def test_set_and_get(self):
        """Тест установки и получения данных из кэша"""
        test_data = pd.DataFrame({'col1': [1, 2, 3], 'col2': ['a', 'b', 'c']})
        
        # Устанавливаем данные
        self.cache.set("test_file.xlsx", "test_sheet", test_data)
        
        # Получаем данные
        cached_data = self.cache.get("test_file.xlsx", "test_sheet")
        
        assert cached_data is not None
        pd.testing.assert_frame_equal(cached_data, test_data)
    
    def test_get_nonexistent(self):
        """Тест получения несуществующих данных"""
        cached_data = self.cache.get("nonexistent_file.xlsx", "nonexistent_sheet")
        assert cached_data is None
    
    def test_clear(self):
        """Тест очистки кэша"""
        test_data = pd.DataFrame({'col1': [1, 2, 3]})
        self.cache.set("test_file.xlsx", "test_sheet", test_data)
        
        # Проверяем, что данные есть
        assert len(self.cache._cache) == 1
        
        # Очищаем кэш
        self.cache.clear()
        
        # Проверяем, что кэш пуст
        assert len(self.cache._cache) == 0
        assert len(self.cache._timestamps) == 0
        assert len(self.cache._file_mod_times) == 0
    
    def test_refresh_file(self):
        """Тест обновления кэша для файла"""
        test_data = pd.DataFrame({'col1': [1, 2, 3]})
        self.cache.set("test_file.xlsx", "test_sheet", test_data)
        
        # Проверяем, что данные есть
        assert len(self.cache._cache) == 1
        
        # Обновляем кэш для файла
        self.cache.refresh_file("test_file.xlsx")
        
        # Проверяем, что данные удалены
        assert len(self.cache._cache) == 0
    
    def test_get_cache_info(self):
        """Тест получения информации о кэше"""
        test_data = pd.DataFrame({'col1': [1, 2, 3]})
        self.cache.set("test_file.xlsx", "test_sheet", test_data)
        
        info = self.cache.get_cache_info()
        
        assert 'cached_files' in info
        assert 'cache_size' in info
        assert 'file_mod_times' in info
        assert info['cache_size'] == 1
        assert 'test_file.xlsx' in info['cached_files']


class TestUtils:
    """Тесты для утилитарных функций"""
    
    def test_find_column(self):
        """Тест поиска колонки по типу"""
        from config import COLUMN_MAPPINGS
        
        # Создаем тестовый DataFrame
        df = pd.DataFrame({
            'price': [100, 200, 300],
            'manager': ['Иван', 'Петр', 'Сидор'],
            'quantity': [1, 2, 3],
            'other_col': ['a', 'b', 'c']
        })
        
        # Тестируем поиск существующих колонок
        assert find_column(df, 'price') == 'price'
        assert find_column(df, 'manager') == 'manager'
        assert find_column(df, 'quantity') == 'quantity'
        
        # Тестируем поиск несуществующих колонок
        assert find_column(df, 'nonexistent') is None
    
    def test_clean_numeric_data(self):
        """Тест очистки числовых данных"""
        # Создаем DataFrame с разными типами данных
        df = pd.DataFrame({
            'col1': [1, 2, '3', '4.5', 'invalid', None, 6],
            'col2': ['a', 'b', 'c', 'd', 'e', 'f', 'g']
        })
        
        # Очищаем числовые данные
        cleaned = clean_numeric_data(df, 'col1')
        
        # Проверяем результат
        assert len(cleaned) == 4  # 1, 2, 3, 4.5, 6 (invalid и None исключены)
        assert cleaned.tolist() == [1.0, 2.0, 3.0, 4.5, 6.0]
    
    def test_split_message_if_long(self):
        """Тест разбивки длинных сообщений"""
        # Короткое сообщение
        short_text = "Короткое сообщение"
        parts = split_message_if_long(short_text)
        assert len(parts) == 1
        assert parts[0] == short_text
        
        # Длинное сообщение
        long_text = "A" * 5000  # 5000 символов
        parts = split_message_if_long(long_text, max_length=1000)
        assert len(parts) == 5  # 5000 / 1000 = 5 частей
        
        # Проверяем, что все части имеют правильную длину
        for part in parts:
            assert len(part) <= 1000
        
        # Проверяем, что объединение дает исходный текст
        assert ''.join(parts) == long_text
    
    def test_split_message_custom_length(self):
        """Тест разбивки сообщений с кастомной длиной"""
        text = "A" * 100
        parts = split_message_if_long(text, max_length=30)
        assert len(parts) == 4  # 100 / 30 = 4 части (с округлением вверх)
        
        # Проверяем длину каждой части
        for part in parts:
            assert len(part) <= 30


class TestUtilsIntegration:
    """Интеграционные тесты для утилит"""
    
    def test_data_cache_with_real_file(self):
        """Тест кэша с реальным файлом"""
        # Создаем временный Excel файл
        with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            # Создаем тестовые данные
            test_data = pd.DataFrame({
                'col1': [1, 2, 3, 4, 5],
                'col2': ['a', 'b', 'c', 'd', 'e']
            })
            
            # Сохраняем в Excel
            test_data.to_excel(temp_file_path, sheet_name='test', index=False)
            
            # Создаем кэш
            cache = DataCache()
            
            # Читаем данные через кэш (первый раз - из файла)
            cached_data = cache.get(temp_file_path, 'test')
            assert cached_data is None  # Первый раз данных нет в кэше
            
            # Устанавливаем данные в кэш
            cache.set(temp_file_path, 'test', test_data)
            
            # Читаем данные из кэша
            cached_data = cache.get(temp_file_path, 'test')
            assert cached_data is not None
            pd.testing.assert_frame_equal(cached_data, test_data)
            
        finally:
            if os.path.exists(temp_file_path):
                os.unlink(temp_file_path)


if __name__ == "__main__":
    pytest.main([__file__])

