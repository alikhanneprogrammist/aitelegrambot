"""
Утилиты для работы с данными
"""
import pandas as pd
import time
import os
from typing import Optional, Dict, Any, List
from config import COLUMN_MAPPINGS, CACHE_DURATION

class DataCache:
    """Умный кэш для Excel данных с отслеживанием изменений файла"""
    def __init__(self):
        self._cache = {}
        self._timestamps = {}
        self._file_mod_times = {}  # Время модификации файлов
    
    def _get_file_mod_time(self, file_path: str) -> float:
        """Получить время модификации файла"""
        try:
            return os.path.getmtime(file_path)
        except OSError:
            return 0.0
    
    def get(self, file_path: str, sheet_name: str) -> Optional[pd.DataFrame]:
        """Получить данные из кэша с проверкой изменений файла"""
        key = f"{file_path}:{sheet_name}"
        
        if key not in self._cache:
            return None
        
        # Проверяем время модификации файла
        current_mod_time = self._get_file_mod_time(file_path)
        cached_mod_time = self._file_mod_times.get(file_path, 0)
        
        # Если файл изменился, очищаем кэш для этого файла
        if current_mod_time > cached_mod_time:
            self._clear_file_cache(file_path)
            return None
        
        # Проверяем, не устарел ли кэш по времени
        if time.time() - self._timestamps[key] > CACHE_DURATION:
            del self._cache[key]
            del self._timestamps[key]
            return None
        
        return self._cache[key]
    
    def set(self, file_path: str, sheet_name: str, data: pd.DataFrame):
        """Сохранить данные в кэш"""
        key = f"{file_path}:{sheet_name}"
        self._cache[key] = data.copy()
        self._timestamps[key] = time.time()
        self._file_mod_times[file_path] = self._get_file_mod_time(file_path)
    
    def _clear_file_cache(self, file_path: str):
        """Очистить кэш для конкретного файла"""
        keys_to_remove = [key for key in self._cache.keys() if key.startswith(f"{file_path}:")]
        for key in keys_to_remove:
            del self._cache[key]
            del self._timestamps[key]
        
        if file_path in self._file_mod_times:
            del self._file_mod_times[file_path]
    
    def clear(self):
        """Очистить весь кэш"""
        self._cache.clear()
        self._timestamps.clear()
        self._file_mod_times.clear()
    
    def refresh_file(self, file_path: str):
        """Принудительно обновить кэш для файла"""
        self._clear_file_cache(file_path)
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Получить информацию о состоянии кэша"""
        return {
            'cached_files': list(set(key.split(':')[0] for key in self._cache.keys())),
            'cache_size': len(self._cache),
            'file_mod_times': self._file_mod_times.copy()
        }

# Глобальный экземпляр кэша
data_cache = DataCache()

def find_column(df: pd.DataFrame, column_type: str) -> Optional[str]:
    """
    Найти колонку определенного типа в DataFrame
    
    Args:
        df: DataFrame для поиска
        column_type: Тип колонки ('price', 'manager', 'rop', etc.)
    
    Returns:
        Название найденной колонки или None
    """
    if column_type not in COLUMN_MAPPINGS:
        return None
    
    possible_columns = COLUMN_MAPPINGS[column_type]
    
    for col in possible_columns:
        if col in df.columns:
            return col
    
    return None

def load_excel_with_cache(file_path: str, sheet_name: str) -> pd.DataFrame:
    """
    Загрузить Excel файл с использованием кэша
    
    Args:
        file_path: Путь к Excel файлу
        sheet_name: Название листа
    
    Returns:
        DataFrame с данными
    """
    # Сначала проверяем кэш
    cached_data = data_cache.get(file_path, sheet_name)
    if cached_data is not None:
        return cached_data
    
    # Если в кэше нет, читаем из файла
    try:
        data = pd.read_excel(file_path, sheet_name=sheet_name)
        data_cache.set(file_path, sheet_name, data)
        return data
    except Exception as e:
        raise Exception(f"Ошибка при чтении Excel файла {file_path}, лист {sheet_name}: {str(e)}")

def validate_excel_structure(df: pd.DataFrame, required_columns: List[str]) -> List[str]:
    """
    Проверить структуру DataFrame на наличие необходимых колонок
    
    Args:
        df: DataFrame для проверки
        required_columns: Список обязательных типов колонок
    
    Returns:
        Список отсутствующих колонок
    """
    missing = []
    
    for col_type in required_columns:
        if find_column(df, col_type) is None:
            missing.append(col_type)
    
    return missing

def clean_numeric_data(df: pd.DataFrame, column: str) -> pd.Series:
    """
    Очистить числовые данные в колонке
    
    Args:
        df: DataFrame
        column: Название колонки
    
    Returns:
        Очищенная Series с числовыми данными
    """
    return pd.to_numeric(df[column], errors='coerce').dropna()

def split_message_if_long(text: str, max_length: int = 4000) -> List[str]:
    """
    Разбить длинное сообщение на части
    
    Args:
        text: Исходный текст
        max_length: Максимальная длина части
    
    Returns:
        Список частей сообщения
    """
    if len(text) <= max_length:
        return [text]
    
    parts = []
    for i in range(0, len(text), max_length):
        parts.append(text[i:i + max_length])
    
    return parts
