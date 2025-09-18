"""
Модуль для AI рекомендаций и анализа трендов
"""
import os
import pandas as pd
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
from openai import OpenAI
from dotenv import load_dotenv

# Добавляем путь к корневой папке для импорта utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_excel_with_cache

load_dotenv()

class AIRecommendations:
    """Класс для AI рекомендаций и анализа трендов"""
    
    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.sales_df = None
        self.salary_df = None
        self.openai_client = None
        self._load_data()
        self._init_openai()
    
    def _load_data(self):
        """Загружает данные о продажах и зарплатах"""
        try:
            self.sales_df = load_excel_with_cache(self.excel_file_path, 'продажи')
            self.salary_df = load_excel_with_cache(self.excel_file_path, 'зарплата')
            # Обрабатываем смешанные типы дат (строки и datetime объекты)
            # Обрабатываем каждую строку отдельно
            processed_dates = []
            for date_val in self.sales_df['date']:
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
            
            self.sales_df['date'] = processed_dates
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    
    def _init_openai(self):
        """Инициализирует OpenAI клиент"""
        try:
            api_key = os.getenv('OPENAI_API_KEY')
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)
            else:
                print("⚠️ OPENAI_API_KEY не найден в .env файле")
        except Exception as e:
            print(f"❌ Ошибка инициализации OpenAI: {e}")
    
    def analyze_trends_and_patterns(self, months_back: int = 6) -> Dict:
        """
        Анализирует тренды и закономерности в данных
        
        Args:
            months_back: Количество месяцев назад для анализа
            
        Returns:
            Dict: Анализ трендов и закономерностей
        """
        try:
            now = datetime.now()
            analysis_data = []
            
            # Анализируем данные за последние месяцы
            for i in range(months_back):
                month_date = now - timedelta(days=30 * i)
                month = month_date.month
                year = month_date.year
                
                month_data = self.sales_df[
                    (self.sales_df['date'].dt.year == year) & 
                    (self.sales_df['date'].dt.month == month)
                ].copy()
                
                if not month_data.empty:
                    total_sales = (month_data['price'] * month_data['quantity']).sum()
                    total_orders = len(month_data)
                    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
                    
                    # Анализ по менеджерам
                    manager_sales = month_data.groupby('manager').agg({
                        'price': lambda x: (x * month_data.loc[x.index, 'quantity']).sum(),
                        'quantity': 'sum',
                        'order': 'count'
                    }).rename(columns={'price': 'sales', 'order': 'orders'})
                    
                    # Анализ по товарам
                    product_sales = month_data.groupby('name_boiler').agg({
                        'price': lambda x: (x * month_data.loc[x.index, 'quantity']).sum(),
                        'quantity': 'sum',
                        'order': 'count'
                    }).rename(columns={'price': 'sales', 'order': 'orders'})
                    
                    analysis_data.append({
                        'month': f"{year}-{month:02d}",
                        'total_sales': total_sales,
                        'total_orders': total_orders,
                        'avg_order_value': avg_order_value,
                        'top_manager': manager_sales['sales'].idxmax() if not manager_sales.empty else None,
                        'top_product': product_sales['sales'].idxmax() if not product_sales.empty else None,
                        'manager_diversity': len(manager_sales),
                        'product_diversity': len(product_sales)
                    })
            
            # Выявляем закономерности
            patterns = self._identify_patterns(analysis_data)
            
            return {
                'status': 'success',
                'analysis_period': f"Последние {months_back} месяцев",
                'monthly_data': analysis_data,
                'patterns': patterns,
                'trends': self._calculate_trends(analysis_data)
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Ошибка анализа трендов: {e}'}
    
    def _identify_patterns(self, data: List[Dict]) -> Dict:
        """Выявляет закономерности в данных"""
        try:
            if len(data) < 2:
                return {'status': 'insufficient_data'}
            
            # Анализ роста/падения продаж
            sales_values = [d['total_sales'] for d in data]
            sales_growth = []
            for i in range(1, len(sales_values)):
                growth = (sales_values[i-1] - sales_values[i]) / sales_values[i] * 100 if sales_values[i] > 0 else 0
                sales_growth.append(growth)
            
            avg_growth = sum(sales_growth) / len(sales_growth) if sales_growth else 0
            
            # Сезонность
            monthly_sales = {}
            for d in data:
                month = d['month'].split('-')[1]
                if month not in monthly_sales:
                    monthly_sales[month] = []
                monthly_sales[month].append(d['total_sales'])
            
            seasonal_pattern = {}
            for month, sales in monthly_sales.items():
                seasonal_pattern[month] = sum(sales) / len(sales) if sales else 0
            
            # Стабильность
            sales_volatility = self._calculate_volatility(sales_values)
            
            return {
                'avg_growth_rate': avg_growth,
                'growth_trend': '📈 Рост' if avg_growth > 5 else '📉 Снижение' if avg_growth < -5 else '➡️ Стабильно',
                'seasonal_pattern': seasonal_pattern,
                'volatility': sales_volatility,
                'stability': 'Стабильно' if sales_volatility < 20 else 'Волатильно'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Ошибка выявления закономерностей: {e}'}
    
    def _calculate_volatility(self, values: List[float]) -> float:
        """Рассчитывает волатильность (стандартное отклонение в процентах)"""
        if len(values) < 2:
            return 0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        std_dev = variance ** 0.5
        return (std_dev / mean * 100) if mean > 0 else 0
    
    def _calculate_trends(self, data: List[Dict]) -> Dict:
        """Рассчитывает тренды"""
        try:
            if len(data) < 2:
                return {'status': 'insufficient_data'}
            
            # Тренд продаж
            sales_values = [d['total_sales'] for d in data]
            sales_trend = self._linear_trend(sales_values)
            
            # Тренд заказов
            orders_values = [d['total_orders'] for d in data]
            orders_trend = self._linear_trend(orders_values)
            
            # Тренд среднего чека
            avg_values = [d['avg_order_value'] for d in data]
            avg_trend = self._linear_trend(avg_values)
            
            return {
                'sales_trend': sales_trend,
                'orders_trend': orders_trend,
                'avg_order_trend': avg_trend
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Ошибка расчета трендов: {e}'}
    
    def _linear_trend(self, values: List[float]) -> Dict:
        """Рассчитывает линейный тренд"""
        if len(values) < 2:
            return {'slope': 0, 'direction': 'stable'}
        
        n = len(values)
        x = list(range(n))
        
        # Простой расчет наклона
        sum_x = sum(x)
        sum_y = sum(values)
        sum_xy = sum(x[i] * values[i] for i in range(n))
        sum_x2 = sum(xi ** 2 for xi in x)
        
        slope = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x ** 2) if (n * sum_x2 - sum_x ** 2) != 0 else 0
        
        direction = 'growth' if slope > 0 else 'decline' if slope < 0 else 'stable'
        
        return {
            'slope': slope,
            'direction': direction,
            'strength': abs(slope) / (sum(values) / n) * 100 if sum(values) > 0 else 0
        }
    
    def get_ai_recommendations(self, focus_area: str = "general") -> str:
        """
        Получает AI рекомендации по увеличению продаж
        
        Args:
            focus_area: Область фокуса (general, sales, efficiency, trends)
            
        Returns:
            str: AI рекомендации
        """
        try:
            if not self.openai_client:
                return "❌ OpenAI недоступен. Проверьте настройки API ключа."
            
            # Получаем данные для анализа
            trends_data = self.analyze_trends_and_patterns(3)
            
            # Создаем промпт для AI
            prompt = self._create_recommendations_prompt(trends_data, focus_area)
            
            # Получаем рекомендации от AI
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system", 
                        "content": "Ты эксперт по анализу продаж и бизнес-консультант. Анализируй данные и давай конкретные, практические рекомендации по увеличению продаж. Отвечай на русском языке, будь кратким и конкретным."
                    },
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1000,
                temperature=0.7
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"❌ Ошибка получения AI рекомендаций: {e}"
    
    def _create_recommendations_prompt(self, trends_data: Dict, focus_area: str) -> str:
        """Создает промпт для AI рекомендаций"""
        
        if trends_data['status'] != 'success':
            return f"Проанализируй общие принципы увеличения продаж в области {focus_area} и дай 5-7 конкретных рекомендаций."
        
        data = trends_data['monthly_data']
        patterns = trends_data['patterns']
        trends = trends_data['trends']
        
        prompt = f"""
        Проанализируй следующие данные о продажах и дай рекомендации по увеличению продаж:
        
        ДАННЫЕ ЗА ПОСЛЕДНИЕ МЕСЯЦЫ:
        {data}
        
        ВЫЯВЛЕННЫЕ ЗАКОНОМЕРНОСТИ:
        - Средний рост: {patterns.get('avg_growth_rate', 0):.1f}%
        - Тренд роста: {patterns.get('growth_trend', 'Неизвестно')}
        - Стабильность: {patterns.get('stability', 'Неизвестно')}
        
        ТРЕНДЫ:
        - Продажи: {trends.get('sales_trend', {}).get('direction', 'Неизвестно')}
        - Заказы: {trends.get('orders_trend', {}).get('direction', 'Неизвестно')}
        - Средний чек: {trends.get('avg_order_trend', {}).get('direction', 'Неизвестно')}
        
        ОБЛАСТЬ ФОКУСА: {focus_area}
        
        Дай 5-7 конкретных, практических рекомендаций по увеличению продаж. Будь кратким и конкретным.
        """
        
        return prompt
    
    def generate_weekly_report(self) -> str:
        """Генерирует еженедельный отчет"""
        try:
            now = datetime.now()
            week_start = now - timedelta(days=now.weekday())
            week_end = week_start + timedelta(days=6)
            
            # Получаем данные за неделю
            week_data = self.sales_df[
                (self.sales_df['date'] >= week_start) & 
                (self.sales_df['date'] <= week_end)
            ].copy()
            
            if week_data.empty:
                return "📊 **ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ**\n\n❌ Нет данных за эту неделю"
            
            total_sales = (week_data['price'] * week_data['quantity']).sum()
            total_orders = len(week_data)
            avg_order = total_sales / total_orders if total_orders > 0 else 0
            
            # Топ менеджер недели
            manager_sales = week_data.groupby('manager').agg({
                'price': lambda x: (x * week_data.loc[x.index, 'quantity']).sum()
            }).rename(columns={'price': 'sales'})
            top_manager = manager_sales['sales'].idxmax() if not manager_sales.empty else "Нет данных"
            
            # Топ товар недели
            product_sales = week_data.groupby('name_boiler').agg({
                'price': lambda x: (x * week_data.loc[x.index, 'quantity']).sum()
            }).rename(columns={'price': 'sales'})
            top_product = product_sales['sales'].idxmax() if not product_sales.empty else "Нет данных"
            
            report = f"""📊 **ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ**
📅 Период: {week_start.strftime('%d.%m')} - {week_end.strftime('%d.%m.%Y')}

💰 **ОСНОВНЫЕ ПОКАЗАТЕЛИ:**
• Общие продажи: {total_sales:,.0f} тенге
• Количество заказов: {total_orders}
• Средний чек: {avg_order:,.0f} тенге

🏆 **ЛУЧШИЕ ПОКАЗАТЕЛИ:**
• Менеджер недели: {top_manager}
• Товар недели: {top_product}

📈 **РЕКОМЕНДАЦИИ:**
{self.get_ai_recommendations('weekly')}
"""
            
            return report
            
        except Exception as e:
            return f"❌ Ошибка генерации еженедельного отчета: {e}"
    
    def generate_monthly_report(self) -> str:
        """Генерирует месячный отчет"""
        try:
            now = datetime.now()
            month_data = self.sales_df[
                (self.sales_df['date'].dt.year == now.year) & 
                (self.sales_df['date'].dt.month == now.month)
            ].copy()
            
            if month_data.empty:
                return "📊 **МЕСЯЧНЫЙ ОТЧЕТ**\n\n❌ Нет данных за этот месяц"
            
            total_sales = (month_data['price'] * month_data['quantity']).sum()
            total_orders = len(month_data)
            avg_order = total_sales / total_orders if total_orders > 0 else 0
            
            # Анализ по менеджерам
            manager_analysis = month_data.groupby('manager').agg({
                'price': lambda x: (x * month_data.loc[x.index, 'quantity']).sum(),
                'quantity': 'sum',
                'order': 'count'
            }).rename(columns={'price': 'sales', 'order': 'orders'})
            
            # Анализ по товарам
            product_analysis = month_data.groupby('name_boiler').agg({
                'price': lambda x: (x * month_data.loc[x.index, 'quantity']).sum(),
                'quantity': 'sum',
                'order': 'count'
            }).rename(columns={'price': 'sales', 'order': 'orders'})
            
            # Топ-3 менеджера
            top_managers = manager_analysis.nlargest(3, 'sales')
            
            # Топ-3 товара
            top_products = product_analysis.nlargest(3, 'sales')
            
            report = f"""📊 **МЕСЯЧНЫЙ ОТЧЕТ**
📅 Месяц: {now.strftime('%B %Y')}

💰 **ОСНОВНЫЕ ПОКАЗАТЕЛИ:**
• Общие продажи: {total_sales:,.0f} тенге
• Количество заказов: {total_orders}
• Средний чек: {avg_order:,.0f} тенге

🏆 **ТОП-3 МЕНЕДЖЕРА:**
"""
            
            for i, (manager, data) in enumerate(top_managers.iterrows(), 1):
                report += f"{i}. {manager}: {data['sales']:,.0f} тенге ({data['orders']} заказов)\n"
            
            report += "\n🏷️ **ТОП-3 ТОВАРА:**\n"
            
            for i, (product, data) in enumerate(top_products.iterrows(), 1):
                report += f"{i}. {product}: {data['sales']:,.0f} тенге ({data['quantity']} шт.)\n"
            
            report += f"\n📈 **AI РЕКОМЕНДАЦИИ:**\n{self.get_ai_recommendations('monthly')}"
            
            return report
            
        except Exception as e:
            return f"❌ Ошибка генерации месячного отчета: {e}"

# Пример использования
if __name__ == "__main__":
    ai = AIRecommendations("Alseit.xlsx")
    
    # Анализ трендов
    trends = ai.analyze_trends_and_patterns()
    print(trends)
    
    # AI рекомендации
    recommendations = ai.get_ai_recommendations()
    print(recommendations)
    
    # Еженедельный отчет
    weekly_report = ai.generate_weekly_report()
    print(weekly_report)
