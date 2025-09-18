"""
Базовый класс для управления расходами
"""
import pandas as pd
import os
from datetime import datetime, date
from openai import OpenAI
import json
import re
from typing import Optional, Tuple, List, Dict, Any


class BaseExpenseManager:
    """Базовый класс для управления расходами"""
    
    def __init__(self, excel_file_path: str, sheet_name: str, 
                 fixed_expenses: List[Dict[str, Any]]):
        """
        Инициализация менеджера расходов
        
        Args:
            excel_file_path: Путь к Excel файлу
            sheet_name: Название листа
            fixed_expenses: Список постоянных расходов
        """
        self.excel_file = excel_file_path
        self.sheet_name = sheet_name
        self.fixed_expenses = fixed_expenses
        
        # Инициализируем OpenAI клиент
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
    
    def add_fixed_expenses_if_needed(self) -> bool:
        """Добавляет постоянные расходы в начале месяца, если их еще нет"""
        try:
            # Читаем текущие данные
            df = self._read_excel_data()
            
            # Получаем текущий месяц и год
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Проверяем, есть ли уже постоянные расходы в этом месяце
            if not df.empty:
                df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', 
                                          errors='coerce')
                current_month_expenses = df[
                    (df['date'].dt.month == current_month) & 
                    (df['date'].dt.year == current_year) &
                    (df['category'].isin([exp['category'] for exp in self.fixed_expenses]))
                ]
                
                if not current_month_expenses.empty:
                    return False  # Постоянные расходы уже добавлены
            
            # Добавляем постоянные расходы
            new_expenses = []
            for expense in self.fixed_expenses:
                new_expenses.append({
                    'date': date.today().strftime('%d.%m.%Y'),
                    'category': expense['category'],
                    'amount': expense['amount'],
                    'payment_method': expense['payment_method'],
                    'comments': expense['comments']
                })
            
            # Добавляем к существующим данным
            new_df = pd.DataFrame(new_expenses)
            if not df.empty:
                combined_df = pd.concat([df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            # Сохраняем обратно в Excel
            self._save_excel_data(combined_df)
            return True
            
        except Exception as e:
            print(f"Ошибка при добавлении постоянных расходов: {e}")
            return False
    
    def categorize_expense(self, text: str) -> Tuple[str, float]:
        """Использует GPT для категоризации расхода"""
        if not self.client:
            return "прочее", 0.5
            
        try:
            prompt = self._create_categorization_prompt(text)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=100
            )
            
            result = json.loads(response.choices[0].message.content)
            return result['category'], result.get('confidence', 0.8)
            
        except Exception as e:
            print(f"Ошибка при категоризации: {e}")
            return "прочее", 0.5
    
    def add_expense_from_voice(self, text: str, amount: Optional[float] = None) -> Tuple[bool, str]:
        """Добавляет расход на основе текста из голосового сообщения"""
        try:
            # Категоризируем расход
            category, confidence = self.categorize_expense(text)
            
            # Извлекаем сумму, если не указана
            if amount is None:
                amount = self._extract_amount_from_text(text)
                if amount is None:
                    return False, "Не удалось определить сумму расхода. Пожалуйста, укажите сумму, например: '5000 еда' или '150к кафе'"
            
            # Определяем способ оплаты
            payment_method = self._determine_payment_method(text)
            
            # Читаем текущие данные
            df = self._read_excel_data()
            
            # Добавляем новый расход
            new_expense = {
                'date': date.today().strftime('%d.%m.%Y'),
                'category': category,
                'amount': amount,
                'payment_method': payment_method,
                'comments': text
            }
            
            new_df = pd.DataFrame([new_expense])
            if not df.empty:
                combined_df = pd.concat([df, new_df], ignore_index=True)
            else:
                combined_df = new_df
            
            # Сохраняем обратно в Excel
            self._save_excel_data(combined_df)
            
            return True, f"Расход добавлен: {category} - {amount} тенге"
            
        except Exception as e:
            print(f"Ошибка при добавлении расхода: {e}")
            return False, f"Ошибка: {str(e)}"
    
    def get_monthly_summary(self, month: Optional[int] = None, 
                           year: Optional[int] = None) -> str:
        """Получает сводку расходов за месяц"""
        try:
            if month is None:
                month = datetime.now().month
            if year is None:
                year = datetime.now().year
            
            df = self._read_excel_data()
            if df.empty:
                return "Нет данных о расходах"
            
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', 
                                      errors='coerce')
            monthly_data = df[
                (df['date'].dt.month == month) & 
                (df['date'].dt.year == year)
            ]
            
            if monthly_data.empty:
                return f"Нет расходов за {month}.{year}"
            
            # Группируем по категориям
            summary = monthly_data.groupby('category')['amount'].sum().sort_values(ascending=False)
            total = summary.sum()
            
            result = f"📊 {self.sheet_name.title()} расходы за {month}.{year}\n\n"
            for category, amount in summary.items():
                percentage = (amount / total) * 100
                result += f"• {category}: {amount:,.0f} ₸ ({percentage:.1f}%)\n"
            
            result += f"\n💰 Общая сумма: {total:,.0f} ₸"
            return result
            
        except Exception as e:
            return f"Ошибка при получении сводки: {str(e)}"
    
    def get_category_breakdown(self) -> str:
        """Получает разбивку по категориям за текущий месяц"""
        return self.get_monthly_summary()
    
    def get_recent_expenses(self, limit: int = 10) -> str:
        """Получает последние расходы"""
        try:
            df = self._read_excel_data()
            if df.empty:
                return f"📋 **ПОСЛЕДНИЕ {self.sheet_name.upper()} РАСХОДЫ**\n\nНет данных"
            
            # Сортируем по дате (последние сверху)
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', 
                                      errors='coerce')
            recent_data = df.sort_values('date', ascending=False).head(limit)
            
            summary = f"📋 **ПОСЛЕДНИЕ {len(recent_data)} {self.sheet_name.upper()} РАСХОДОВ**\n\n"
            
            for _, row in recent_data.iterrows():
                date_str = row['date'].strftime('%d.%m.%Y') if pd.notna(row['date']) else 'Неизвестно'
                summary += f"• {date_str} | {row['category']} | {row['amount']:,.0f} тенге\n"
                if pd.notna(row['comments']) and row['comments'].strip():
                    summary += f"  💬 {row['comments']}\n"
                summary += "\n"
            
            return summary
            
        except Exception as e:
            return f"❌ Ошибка при получении расходов: {e}"
    
    def get_weekly_summary(self) -> str:
        """Получает сводку за текущую неделю"""
        try:
            from datetime import timedelta
            df = self._read_excel_data()
            if df.empty:
                return f"📊 **СВОДКА {self.sheet_name.upper()} РАСХОДОВ ЗА НЕДЕЛЮ**\n\nНет данных"
            
            # Получаем начало и конец текущей недели
            today = datetime.now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', 
                                      errors='coerce')
            start_of_week_dt = pd.Timestamp(start_of_week)
            end_of_week_dt = pd.Timestamp(end_of_week) + pd.Timedelta(days=1)
            
            weekly_data = df[
                (df['date'] >= start_of_week_dt) & 
                (df['date'] < end_of_week_dt)
            ]
            
            if weekly_data.empty:
                return f"📊 **СВОДКА {self.sheet_name.upper()} РАСХОДОВ ЗА НЕДЕЛЮ ({start_of_week.strftime('%d.%m')} - {end_of_week.strftime('%d.%m')})**\n\nНет данных за эту неделю"
            
            # Группируем по категориям
            category_summary = weekly_data.groupby('category')['amount'].sum().sort_values(ascending=False)
            total_amount = weekly_data['amount'].sum()
            
            summary = f"📊 **СВОДКА {self.sheet_name.upper()} РАСХОДОВ ЗА НЕДЕЛЮ ({start_of_week.strftime('%d.%m')} - {end_of_week.strftime('%d.%m')})**\n\n"
            summary += f"💰 **Общая сумма:** {total_amount:,.0f} тенге\n\n"
            summary += "📋 **По категориям:**\n"
            
            for category, amount in category_summary.items():
                percentage = (amount / total_amount) * 100
                summary += f"• {category}: {amount:,.0f} тенге ({percentage:.1f}%)\n"
            
            return summary
            
        except Exception as e:
            return f"❌ Ошибка при получении недельной сводки: {e}"
    
    def get_gpt_analysis(self) -> str:
        """Получает GPT анализ трат с рекомендациями"""
        if not self.client:
            return f"🤖 **GPT АНАЛИЗ {self.sheet_name.upper()} РАСХОДОВ**\n\nOpenAI API недоступен"
            
        try:
            from datetime import timedelta
            df = self._read_excel_data()
            if df.empty:
                return f"🤖 **GPT АНАЛИЗ {self.sheet_name.upper()} РАСХОДОВ**\n\nНет данных для анализа"
            
            # Получаем данные за последние 30 дней
            thirty_days_ago = datetime.now() - timedelta(days=30)
            df['date'] = pd.to_datetime(df['date'], format='%d.%m.%Y', 
                                      errors='coerce')
            recent_data = df[df['date'] >= thirty_days_ago]
            
            if recent_data.empty:
                return f"🤖 **GPT АНАЛИЗ {self.sheet_name.upper()} РАСХОДОВ**\n\nНедостаточно данных для анализа (нужно минимум 30 дней)"
            
            # Подготавливаем данные для анализа
            category_summary = recent_data.groupby('category')['amount'].sum().sort_values(ascending=False)
            total_amount = recent_data['amount'].sum()
            
            # Создаем промпт для GPT
            prompt = self._create_analysis_prompt(category_summary, total_amount)
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=300
            )
            
            analysis = response.choices[0].message.content.strip()
            return f"🤖 **GPT АНАЛИЗ {self.sheet_name.upper()} РАСХОДОВ**\n\n{analysis}"
            
        except Exception as e:
            return f"❌ Ошибка при получении анализа: {e}"
    
    def edit_last_expense(self, new_category: Optional[str] = None, 
                         new_amount: Optional[float] = None) -> Tuple[bool, str]:
        """Редактирует последний добавленный расход"""
        try:
            df = self._read_excel_data()
            if df.empty:
                return False, "Нет расходов для редактирования"
            
            # Получаем последний расход
            last_index = len(df) - 1
            last_expense = df.iloc[last_index].copy()
            
            # Обновляем данные
            if new_category:
                df.at[last_index, 'category'] = new_category
            if new_amount:
                df.at[last_index, 'amount'] = new_amount
            
            # Сохраняем изменения
            self._save_excel_data(df)
            
            return True, f"{self.sheet_name.title()} расход обновлен: {df.at[last_index, 'category']} - {df.at[last_index, 'amount']:,.0f} тенге"
            
        except Exception as e:
            return False, f"Ошибка при редактировании: {e}"
    
    def _read_excel_data(self) -> pd.DataFrame:
        """Читает данные из Excel файла"""
        try:
            return pd.read_excel(self.excel_file, sheet_name=self.sheet_name)
        except Exception:
            return pd.DataFrame(columns=['date', 'category', 'amount', 'payment_method', 'comments'])
    
    def _save_excel_data(self, df: pd.DataFrame) -> None:
        """Сохраняет данные в Excel файл"""
        with pd.ExcelWriter(self.excel_file, engine='openpyxl', mode='a', 
                          if_sheet_exists='replace') as writer:
            df.to_excel(writer, sheet_name=self.sheet_name, index=False)
    
    def _extract_amount_from_text(self, text: str) -> Optional[float]:
        """Извлекает сумму из текста"""
        # Ищем суммы в разных форматах: 150к, 150000, 1.5к, 1500
        amount_match = re.search(r'(\d+(?:\.\d+)?)\s*к', text, re.IGNORECASE)
        if amount_match:
            return float(amount_match.group(1)) * 1000
        else:
            amount_match = re.search(r'(\d+(?:\.\d+)?)', text)
            if amount_match:
                return float(amount_match.group(1))
        return None
    
    def _determine_payment_method(self, text: str) -> str:
        """Определяет способ оплаты из текста"""
        if any(word in text.lower() for word in ['наличные', 'наличкой', 'деньги']):
            return "наличные"
        return "карта"
    
    def _create_categorization_prompt(self, text: str) -> str:
        """Создает промпт для категоризации (переопределяется в наследниках)"""
        return f"Категоризируй расход: {text}"
    
    def _create_analysis_prompt(self, category_summary: pd.Series, 
                               total_amount: float) -> str:
        """Создает промпт для анализа (переопределяется в наследниках)"""
        return f"Проанализируй расходы: {total_amount} тенге"
