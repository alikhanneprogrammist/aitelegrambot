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

# === ФУНКЦИИ ДЛЯ РАБОТЫ С ПРИБЫЛЬЮ ===

def get_gross_profit(excel_file_path: str = None) -> float:
    """
    Получить прибыль за месяц (чистая прибыль от всех продаж - офисные расходы)
    
    Args:
        excel_file_path: Путь к Excel файлу
    
    Returns:
        Прибыль за месяц в тенге
    """
    try:
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "Alseit.xlsx")
        
        print(f"📁 Загружаем данные из: {excel_file_path}")
        
        # Загружаем данные о продажах
        sales_df = load_excel_with_cache(excel_file_path, 'продажи')
        
        if sales_df.empty:
            print("❌ Данные о продажах пусты")
            return 0.0
        
        # Получаем текущий месяц и год
        current_date = pd.Timestamp.now()
        current_month = current_date.month
        current_year = current_date.year
        
        print(f"📅 Текущая дата: {current_date.strftime('%Y-%m-%d')}")
        print(f"📅 Ищем продажи за: {current_month}.{current_year}")
        
        # Фильтруем продажи за текущий месяц (исправляем формат даты DD.MM.YYYY)
        sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
        monthly_sales = sales_df[
            (sales_df['date'].dt.month == current_month) & 
            (sales_df['date'].dt.year == current_year)
        ]
        
        if monthly_sales.empty:
            print("❌ Нет продаж за текущий месяц")
            return 0.0
        
        print(f"📊 Найдено продаж за текущий месяц: {len(monthly_sales)}")
        
        # Рассчитываем чистую прибыль от каждой продажи
        total_net_profit = 0.0
        
        for idx, row in monthly_sales.iterrows():
            boiler_name = str(row.get('boiler_name', '')).strip()  # Очищаем пробелы
            price = row.get('price', 0)
            quantity = row.get('quantity', 1)
            payment_method = row.get('payment_method', 'наличные')
            accessories = row.get('accessories', 0)
            purchase = row.get('purchase', 0)  # Используем закупочную цену из таблицы
            
            if pd.isna(boiler_name) or boiler_name == '' or boiler_name == 'nan':
                continue
                
            # Получаем данные котла для расчета бонусов
            from salary_folder.salary_update import BOILER_PRICES, LOW_DEDUCTION_BOILERS, LOW_DEDUCTION_AMOUNT, HIGH_DEDUCTION_AMOUNT, MANAGER_BONUS_RATE, BANK_TAX_RATE
            
            if boiler_name not in BOILER_PRICES:
                print(f"⚠️ Котел {boiler_name} не найден в BOILER_PRICES")
                continue
                
            boiler_data = BOILER_PRICES[boiler_name]
            boiler_price = boiler_data['price']
            
            if boiler_price == 0:
                continue
            
            # Общая стоимость (используем цену из таблицы продаж)
            # Преобразуем в числа и проверяем на валидность
            try:
                price = float(price) if pd.notna(price) else 0
                quantity = float(quantity) if pd.notna(quantity) else 1
                purchase = float(purchase) if pd.notna(purchase) else 0
                accessories = float(accessories) if pd.notna(accessories) else 0
            except (ValueError, TypeError):
                print(f"⚠️ Некорректные данные для {boiler_name}: price={price}, quantity={quantity}")
                continue
                
            total_price = price * quantity
            total_purchase = purchase * quantity
            
            # Определяем сумму доставки для расчета бонусов
            if boiler_name in LOW_DEDUCTION_BOILERS:
                delivery_for_bonus = LOW_DEDUCTION_AMOUNT  # 50,000
            else:
                delivery_for_bonus = HIGH_DEDUCTION_AMOUNT  # 100,000
            
            # Рассчитываем бонус менеджера
            manager_bonus = (total_price - delivery_for_bonus) * MANAGER_BONUS_RATE
            
            # Рассчитываем чистую прибыль от этой продажи
            profit = total_price
            
            # Вычитаем 12% если оплата через банк
            if payment_method in ['банк', 'kaspi_pay', 'kaspi_magazine']:
                bank_tax = total_price * BANK_TAX_RATE
                profit -= bank_tax
            
            # Вычитаем 4% налог
            tax_4_percent = total_price * 0.04
            profit -= tax_4_percent
            
            # Вычитаем бонус менеджера
            profit -= manager_bonus
            
            # Вычитаем закупочную стоимость
            profit -= total_purchase
            
            # Вычитаем аксессуары
            profit -= accessories
            
            total_net_profit += profit
            
            print(f"🔧 {boiler_name}: цена={total_price:,.0f}, закупка={total_purchase:,.0f}, прибыль={profit:,.0f}")
        
        print(f"💰 Общая чистая прибыль от продаж: {total_net_profit:,.0f} тенге")
        
        # Отнимаем офисные расходы
        office_expenses = get_office_expenses_total()
        print(f"🏢 Офисные расходы: {office_expenses:,.0f} тенге")
        
        final_profit = total_net_profit - office_expenses
        print(f"💸 Итоговая прибыль за месяц: {final_profit:,.0f} тенге")
        
        return max(0.0, final_profit)  # Не может быть отрицательной
        
    except Exception as e:
        print(f"❌ Ошибка расчета прибыли за месяц: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

def get_net_profit_from_sales(excel_file_path: str = None) -> float:
    """Получить чистую прибыль от продаж за текущий месяц (БЕЗ вычета офисных расходов)"""
    try:
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "Alseit.xlsx")
        
        # Импортируем константы
        from salary_folder.salary_update import BOILER_PRICES, LOW_DEDUCTION_BOILERS, LOW_DEDUCTION_AMOUNT, HIGH_DEDUCTION_AMOUNT, MANAGER_BONUS_RATE, BANK_TAX_RATE
        
        # Загружаем данные о продажах
        sales_df = load_excel_with_cache(excel_file_path, 'продажи')
        
        if sales_df.empty:
            print("📊 Нет данных о продажах")
            return 0.0
        
        # Преобразуем дату в правильный формат (обрабатываем смешанные типы)
        # Обрабатываем каждую строку отдельно
        processed_dates = []
        for date_val in sales_df['date']:
            if pd.isna(date_val):
                processed_dates.append(pd.NaT)
            elif isinstance(date_val, pd.Timestamp):
                # Уже datetime объект
                processed_dates.append(date_val)
            else:
                # Строка, нужно парсить
                date_str = str(date_val)
                # Исправляем ошибки в датах (например, 09.009.2025 -> 09.09.2025)
                import re
                date_str = re.sub(r'\.0+(\d)\.', r'.\1.', date_str)
                try:
                    parsed_date = pd.to_datetime(date_str, format='%d.%m.%Y', errors='coerce')
                    processed_dates.append(parsed_date)
                except:
                    processed_dates.append(pd.NaT)
        
        sales_df['date'] = processed_dates
        
        # Получаем текущий месяц и год
        current_date = pd.Timestamp.now()
        current_month = current_date.month
        current_year = current_date.year
        
        print(f"📅 Текущая дата: {current_date.strftime('%Y-%m-%d')}")
        print(f"📅 Ищем продажи за: {current_month}.{current_year}")
        
        # Фильтруем продажи за текущий месяц
        current_month_sales = sales_df[
            (sales_df['date'].dt.month == current_month) & 
            (sales_df['date'].dt.year == current_year)
        ]
        
        print(f"📊 Найдено продаж за текущий месяц: {len(current_month_sales)}")
        
        total_net_profit = 0.0
        
        for _, row in current_month_sales.iterrows():
            boiler_name = str(row.get('boiler_name', '')).strip()
            
            if not boiler_name or boiler_name == 'nan' or boiler_name not in BOILER_PRICES:
                continue
                
            boiler_data = BOILER_PRICES[boiler_name]
            boiler_price = boiler_data['price']
            
            if boiler_price == 0:
                continue
            
            # Получаем данные из строки
            price = row.get('price', 0)
            quantity = row.get('quantity', 1)
            purchase = row.get('purchase', 0)
            accessories = row.get('accessories', 0)
            payment_method = str(row.get('payment_method', 'наличные')).strip().lower()
            
            # Обрабатываем payment_method
            if payment_method in ['нал', 'наличные', 'наличка', 'cash']:
                payment_method = 'наличные'
            elif payment_method in ['банк', 'банковский', 'карта', 'bank', 'card']:
                payment_method = 'банк'
            else:
                payment_method = 'наличные'
            
            # Преобразуем в числа и проверяем на валидность
            try:
                price = float(price) if pd.notna(price) else 0
                quantity = float(quantity) if pd.notna(quantity) else 1
                purchase = float(purchase) if pd.notna(purchase) else 0
                accessories = float(accessories) if pd.notna(accessories) else 0
            except (ValueError, TypeError):
                print(f"⚠️ Некорректные данные для {boiler_name}: price={price}, quantity={quantity}")
                continue
                
            total_price = price * quantity
            total_purchase = purchase * quantity
            
            # Определяем сумму доставки для расчета бонусов
            if boiler_name in LOW_DEDUCTION_BOILERS:
                delivery_for_bonus = LOW_DEDUCTION_AMOUNT  # 50,000
            else:
                delivery_for_bonus = HIGH_DEDUCTION_AMOUNT  # 100,000
            
            # Рассчитываем бонус менеджера
            manager_bonus = (total_price - delivery_for_bonus) * MANAGER_BONUS_RATE
            
            # Рассчитываем чистую прибыль от этой продажи
            profit = total_price
            
            # Вычитаем 12% если оплата через банк
            if payment_method in ['банк', 'kaspi_pay', 'kaspi_magazine']:
                bank_tax = total_price * BANK_TAX_RATE
                profit -= bank_tax
            
            # Вычитаем 4% налог
            tax_4_percent = total_price * 0.04
            profit -= tax_4_percent
            
            # Вычитаем бонус менеджера
            profit -= manager_bonus
            
            # Вычитаем закупочную стоимость
            profit -= total_purchase
            
            # Вычитаем аксессуары
            profit -= accessories
            
            total_net_profit += profit
            
            print(f"🔧 {boiler_name}: цена={total_price:,.0f}, закупка={total_purchase:,.0f}, прибыль={profit:,.0f}")
        
        print(f"💰 Общая чистая прибыль от продаж: {total_net_profit:,.0f} тенге")
        
        return total_net_profit
        
    except Exception as e:
        print(f"❌ Ошибка расчета чистой прибыли от продаж: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

def get_net_profit(excel_file_path: str = None) -> float:
    """
    Получить чистую прибыль за текущий месяц (сумма чистой прибыли от всех продаж - офисные расходы)
    
    Args:
        excel_file_path: Путь к Excel файлу
    
    Returns:
        Чистая прибыль в тенге
    """
    try:
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "Alseit.xlsx")
        
        print(f"📁 Загружаем данные из: {excel_file_path}")
        
        # Загружаем данные о продажах
        sales_df = load_excel_with_cache(excel_file_path, 'продажи')
        
        if sales_df.empty:
            print("❌ Данные о продажах пусты")
            return 0.0
        
        # Получаем текущий месяц и год
        current_date = pd.Timestamp.now()
        current_month = current_date.month
        current_year = current_date.year
        
        print(f"📅 Текущая дата: {current_date.strftime('%Y-%m-%d')}")
        print(f"📅 Ищем продажи за: {current_month}.{current_year}")
        
        # Фильтруем продажи за текущий месяц
        sales_df['date'] = pd.to_datetime(sales_df['date'], errors='coerce')
        monthly_sales = sales_df[
            (sales_df['date'].dt.month == current_month) & 
            (sales_df['date'].dt.year == current_year)
        ]
        
        if monthly_sales.empty:
            print("❌ Нет продаж за текущий месяц")
            return 0.0
        
        print(f"📊 Найдено продаж за текущий месяц: {len(monthly_sales)}")
        
        # Рассчитываем чистую прибыль от каждой продажи
        total_net_profit = 0.0
        
        for idx, row in monthly_sales.iterrows():
            boiler_name = row.get('boiler_name', '')
            price = row.get('price', 0)
            quantity = row.get('quantity', 1)
            payment_method = row.get('payment_method', 'наличные')
            accessories = row.get('accessories', 0)
            
            if pd.isna(boiler_name) or boiler_name == '':
                continue
                
            # Получаем данные котла
            from salary_folder.salary_update import BOILER_PRICES, LOW_DEDUCTION_BOILERS, LOW_DEDUCTION_AMOUNT, HIGH_DEDUCTION_AMOUNT, MANAGER_BONUS_RATE, BANK_TAX_RATE
            
            if boiler_name not in BOILER_PRICES:
                continue
                
            boiler_data = BOILER_PRICES[boiler_name]
            boiler_price = boiler_data['price']
            purchase = boiler_data['purchase']
            
            if boiler_price == 0:
                continue
            
            # Общая стоимость
            total_price = boiler_price * quantity
            total_purchase = purchase * quantity
            
            # Определяем сумму доставки для расчета бонусов
            if boiler_name in LOW_DEDUCTION_BOILERS:
                delivery_for_bonus = LOW_DEDUCTION_AMOUNT  # 50,000
            else:
                delivery_for_bonus = HIGH_DEDUCTION_AMOUNT  # 100,000
            
            # Рассчитываем бонус менеджера
            manager_bonus = (total_price - delivery_for_bonus) * MANAGER_BONUS_RATE
            
            # Рассчитываем чистую прибыль от этой продажи
            profit = total_price
            
            # Вычитаем 12% если оплата через банк
            if payment_method in ['банк', 'kaspi_pay', 'kaspi_magazine']:
                bank_tax = total_price * BANK_TAX_RATE
                profit -= bank_tax
            
            # Вычитаем 4% налог
            tax_4_percent = total_price * 0.04
            profit -= tax_4_percent
            
            # Вычитаем бонус менеджера
            profit -= manager_bonus
            
            # Вычитаем закупочную стоимость
            profit -= total_purchase
            
            # Вычитаем аксессуары
            profit -= accessories
            
            total_net_profit += profit
            
            print(f"🔧 {boiler_name}: цена={total_price:,.0f}, прибыль={profit:,.0f}")
        
        print(f"💰 Общая чистая прибыль от продаж: {total_net_profit:,.0f} тенге")
        
        # Теперь отнимаем офисные расходы
        office_expenses = get_office_expenses_total()
        print(f"🏢 Офисные расходы: {office_expenses:,.0f} тенге")
        
        final_net_profit = total_net_profit - office_expenses
        print(f"💸 Итоговая чистая прибыль: {final_net_profit:,.0f} тенге")
        
        return max(0.0, final_net_profit)  # Не может быть отрицательной
        
    except Exception as e:
        print(f"❌ Ошибка расчета чистой прибыли: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

def get_office_expenses_total(excel_file_path: str = None) -> float:
    """
    Получить общую сумму офисных расходов за текущий месяц
    
    Args:
        excel_file_path: Путь к Excel файлу
    
    Returns:
        Общая сумма офисных расходов в тенге
    """
    try:
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "expenses.xlsx")
        
        # Загружаем данные об офисных расходах
        office_df = load_excel_with_cache(excel_file_path, 'office')
        
        if office_df.empty:
            return 0.0
        
        # Получаем текущий месяц и год
        current_date = pd.Timestamp.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Фильтруем расходы за текущий месяц
        office_df['date'] = pd.to_datetime(office_df['date'], format='%d.%m.%Y', errors='coerce')
        monthly_expenses = office_df[
            (office_df['date'].dt.month == current_month) & 
            (office_df['date'].dt.year == current_year)
        ]
        
        if monthly_expenses.empty:
            return 0.0
        
        # Рассчитываем общую сумму расходов
        total_expenses = monthly_expenses['amount'].sum()
        
        return float(total_expenses)
        
    except Exception as e:
        print(f"❌ Ошибка расчета офисных расходов: {e}")
        return 0.0

def get_office_summary(excel_file_path: str = None) -> str:
    """
    Получить сводку офисных расходов за текущий месяц
    
    Args:
        excel_file_path: Путь к Excel файлу
    
    Returns:
        Текстовая сводка расходов
    """
    try:
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "expenses.xlsx")
        
        # Загружаем данные об офисных расходах
        office_df = load_excel_with_cache(excel_file_path, 'office')
        
        if office_df.empty:
            return "Нет данных об офисных расходах"
        
        # Получаем текущий месяц и год
        current_date = pd.Timestamp.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Фильтруем расходы за текущий месяц
        office_df['date'] = pd.to_datetime(office_df['date'], format='%d.%m.%Y', errors='coerce')
        monthly_expenses = office_df[
            (office_df['date'].dt.month == current_month) & 
            (office_df['date'].dt.year == current_year)
        ]
        
        if monthly_expenses.empty:
            return f"Нет офисных расходов за {current_month}.{current_year}"
        
        # Группируем по категориям
        summary = monthly_expenses.groupby('category')['amount'].sum().sort_values(ascending=False)
        total = summary.sum()
        
        result = f"🏢 Офисные расходы за {current_month}.{current_year}\n\n"
        for category, amount in summary.items():
            percentage = (amount / total) * 100
            result += f"• {category}: {amount:,.0f} ₸ ({percentage:.1f}%)\n"
        
        result += f"\n💰 Общая сумма: {total:,.0f} ₸"
        return result
        
    except Exception as e:
        return f"Ошибка при получении сводки: {str(e)}"

def add_office_constants(excel_file_path: str = None) -> str:
    """
    Добавить постоянные офисные расходы в начале месяца
    
    Args:
        excel_file_path: Путь к Excel файлу
    
    Returns:
        Результат добавления расходов
    """
    try:
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "expenses.xlsx")
        
        # Постоянные офисные расходы
        fixed_expenses = [
            {"category": "аренда офиса", "amount": 450000, "payment_method": "карта", "comments": ""},
            {"category": "коммунальные услуги", "amount": 129000, "payment_method": "карта", "comments": "офис"},
            {"category": "вода", "amount": 8800, "payment_method": "карта", "comments": ""},
            {"category": "уборка офиса", "amount": 24000, "payment_method": "карта", "comments": ""}
        ]
        
        # Загружаем существующие данные
        try:
            office_df = load_excel_with_cache(excel_file_path, 'office')
        except:
            office_df = pd.DataFrame(columns=['date', 'category', 'amount', 'payment_method', 'comments'])
        
        # Получаем текущий месяц и год
        current_date = pd.Timestamp.now()
        current_month = current_date.month
        current_year = current_date.year
        
        # Проверяем, не добавлены ли уже расходы в этом месяце
        office_df['date'] = pd.to_datetime(office_df['date'], errors='coerce')
        monthly_expenses = office_df[
            (office_df['date'].dt.month == current_month) & 
            (office_df['date'].dt.year == current_year)
        ]
        
        if not monthly_expenses.empty:
            return f"Постоянные расходы уже добавлены за {current_month}.{current_year}"
        
        # Добавляем постоянные расходы
        new_expenses = []
        for expense in fixed_expenses:
            new_expense = {
                'date': current_date.strftime('%d.%m.%Y'),
                'category': expense['category'],
                'amount': expense['amount'],
                'payment_method': expense['payment_method'],
                'comments': expense['comments']
            }
            new_expenses.append(new_expense)
        
        # Добавляем новые расходы к существующим
        new_df = pd.DataFrame(new_expenses)
        office_df = pd.concat([office_df, new_df], ignore_index=True)
        
        # Сохраняем в Excel
        with pd.ExcelWriter(excel_file_path, mode='a', if_sheet_exists='replace') as writer:
            office_df.to_excel(writer, sheet_name='office', index=False)
        
        # Очищаем кэш
        data_cache.refresh_file(excel_file_path)
        
        total_amount = sum(expense['amount'] for expense in fixed_expenses)
        return f"✅ Добавлены постоянные расходы на сумму {total_amount:,.0f} ₸ за {current_month}.{current_year}"
        
    except Exception as e:
        return f"❌ Ошибка добавления постоянных расходов: {str(e)}"