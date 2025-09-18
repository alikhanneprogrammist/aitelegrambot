"""
Модуль для управления зарплатами и анализа эффективности
"""
import os
import pandas as pd
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional

# Добавляем путь к корневой папке для импорта utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import load_excel_with_cache

class SalaryManagement:
    """Класс для управления зарплатами и анализа эффективности"""
    
    def __init__(self, excel_file_path: str):
        self.excel_file_path = excel_file_path
        self.sales_df = None
        self.salary_df = None
        self._load_data()
    
    def _load_data(self):
        """Загружает данные о продажах и зарплатах"""
        try:
            self.sales_df = load_excel_with_cache(self.excel_file_path, 'продажи')
            self.salary_df = load_excel_with_cache(self.excel_file_path, 'зарплата')
            self.sales_df['date'] = pd.to_datetime(self.sales_df['date'], format='%d.%m.%Y', errors='coerce')
        except Exception as e:
            print(f"❌ Ошибка загрузки данных: {e}")
    
    def get_base_salary_row(self) -> pd.Series:
        """Получает строку с базовыми окладами (order = 0)"""
        try:
            base_row = self.salary_df[self.salary_df['order'] == 0]
            if base_row.empty:
                return None
            return base_row.iloc[0]
        except Exception as e:
            print(f"❌ Ошибка получения базовых окладов: {e}")
            return None
    
    def update_base_salary(self, employee_name: str, new_salary: float) -> bool:
        """
        Обновляет базовый оклад сотрудника
        
        Args:
            employee_name: Имя сотрудника
            new_salary: Новый оклад
            
        Returns:
            bool: True если оклад успешно обновлен
        """
        try:
            if employee_name not in self.salary_df.columns:
                print(f"❌ Сотрудник '{employee_name}' не найден в данных о зарплатах")
                return False
            
            # Находим строку с базовыми окладами
            base_row_index = self.salary_df[self.salary_df['order'] == 0].index
            if base_row_index.empty:
                print("❌ Строка с базовыми окладами не найдена")
                return False
            
            # Обновляем оклад
            self.salary_df.loc[base_row_index[0], employee_name] = new_salary
            
            # Сохраняем изменения в Excel
            with pd.ExcelWriter(self.excel_file_path, mode='a', if_sheet_exists='replace') as writer:
                self.salary_df.to_excel(writer, sheet_name='зарплата', index=False)
            
            print(f"✅ Оклад {employee_name} обновлен на {new_salary:,.0f} тенге")
            return True
            
        except Exception as e:
            print(f"❌ Ошибка обновления оклада: {e}")
            return False
    
    def get_detailed_salary_report(self, month: int = None, year: int = None) -> Dict:
        """
        Создает детальную ведомость по сотрудникам
        
        Args:
            month: Месяц (по умолчанию - текущий)
            year: Год (по умолчанию - текущий)
            
        Returns:
            Dict: Детальная ведомость
        """
        try:
            if month is None or year is None:
                now = datetime.now()
                month = month or now.month
                year = year or now.year
            
            # Получаем данные о продажах за месяц
            month_sales = self.sales_df[
                (self.sales_df['date'].dt.year == year) & 
                (self.sales_df['date'].dt.month == month)
            ].copy()
            
            # Получаем базовые оклады
            base_salaries = self.get_base_salary_row()
            if base_salaries is None:
                return {'status': 'error', 'message': 'Базовые оклады не найдены'}
            
            # Исключаем служебные колонки
            exclude_cols = ['date', 'order', 'developer', 'employee ROP', 'assistant', 'assistant 2', 'supplier manager']
            employee_cols = [col for col in self.salary_df.columns if col not in exclude_cols]
            
            # Рассчитываем бонусы для каждого сотрудника
            employee_report = {}
            
            for employee in employee_cols:
                base_salary = base_salaries[employee] if pd.notna(base_salaries[employee]) else 0
                
                # Рассчитываем бонусы от продаж
                employee_sales = month_sales[month_sales['manager'] == employee]
                total_bonus = 0
                
                for _, sale in employee_sales.iterrows():
                    # Упрощенный расчет бонуса (5% от продаж)
                    sale_amount = sale['price'] * sale['quantity']
                    bonus = sale_amount * 0.05
                    total_bonus += bonus
                
                # ROP бонусы (1% от всех продаж)
                rop_bonus = 0
                if employee in ['employee ROP']:
                    total_sales = (month_sales['price'] * month_sales['quantity']).sum()
                    rop_bonus = total_sales * 0.01
                
                total_salary = base_salary + total_bonus + rop_bonus
                
                employee_report[employee] = {
                    'base_salary': base_salary,
                    'sales_bonus': total_bonus,
                    'rop_bonus': rop_bonus,
                    'total_salary': total_salary,
                    'sales_count': len(employee_sales),
                    'total_sales': (employee_sales['price'] * employee_sales['quantity']).sum() if not employee_sales.empty else 0
                }
            
            return {
                'status': 'success',
                'month': f"{year}-{month:02d}",
                'employees': employee_report,
                'total_payroll': sum(emp['total_salary'] for emp in employee_report.values())
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Ошибка создания ведомости: {e}'}
    
    def get_efficiency_analysis(self, month: int = None, year: int = None) -> Dict:
        """
        Анализ эффективности: зарплата vs прибыль от сотрудника
        
        Args:
            month: Месяц (по умолчанию - текущий)
            year: Год (по умолчанию - текущий)
            
        Returns:
            Dict: Анализ эффективности
        """
        try:
            if month is None or year is None:
                now = datetime.now()
                month = month or now.month
                year = year or now.year
            
            # Получаем детальную ведомость
            salary_report = self.get_detailed_salary_report(month, year)
            if salary_report['status'] != 'success':
                return salary_report
            
            # Рассчитываем эффективность для каждого сотрудника
            efficiency_analysis = {}
            
            for employee, data in salary_report['employees'].items():
                if data['total_sales'] > 0:
                    # ROI = (Прибыль от продаж - Зарплата) / Зарплата * 100
                    # Упрощенный расчет: считаем 20% прибыли от продаж
                    estimated_profit = data['total_sales'] * 0.2
                    roi = ((estimated_profit - data['total_salary']) / data['total_salary'] * 100) if data['total_salary'] > 0 else 0
                    
                    # Эффективность продаж на тенге зарплаты
                    sales_per_salary = data['total_sales'] / data['total_salary'] if data['total_salary'] > 0 else 0
                    
                    efficiency_analysis[employee] = {
                        'total_salary': data['total_salary'],
                        'total_sales': data['total_sales'],
                        'estimated_profit': estimated_profit,
                        'roi_percent': roi,
                        'sales_per_salary': sales_per_salary,
                        'efficiency_rating': self._get_efficiency_rating(roi, sales_per_salary)
                    }
            
            # Сортируем по эффективности
            sorted_efficiency = sorted(
                efficiency_analysis.items(), 
                key=lambda x: x[1]['roi_percent'], 
                reverse=True
            )
            
            return {
                'status': 'success',
                'month': f"{year}-{month:02d}",
                'efficiency_analysis': dict(sorted_efficiency),
                'top_performer': sorted_efficiency[0] if sorted_efficiency else None,
                'average_roi': sum(emp['roi_percent'] for emp in efficiency_analysis.values()) / len(efficiency_analysis) if efficiency_analysis else 0
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Ошибка анализа эффективности: {e}'}
    
    def _get_efficiency_rating(self, roi: float, sales_per_salary: float) -> str:
        """Определяет рейтинг эффективности сотрудника"""
        if roi > 100 and sales_per_salary > 5:
            return "🌟 Отличная"
        elif roi > 50 and sales_per_salary > 3:
            return "✅ Хорошая"
        elif roi > 0 and sales_per_salary > 1:
            return "⚠️ Удовлетворительная"
        else:
            return "❌ Низкая"
    
    def get_salary_trends(self, months_back: int = 6) -> Dict:
        """
        Анализ трендов зарплат за последние месяцы
        
        Args:
            months_back: Количество месяцев назад для анализа
            
        Returns:
            Dict: Тренды зарплат
        """
        try:
            now = datetime.now()
            trends_data = []
            
            for i in range(months_back):
                month_date = now - timedelta(days=30 * i)
                month = month_date.month
                year = month_date.year
                
                salary_report = self.get_detailed_salary_report(month, year)
                if salary_report['status'] == 'success':
                    trends_data.append({
                        'month': f"{year}-{month:02d}",
                        'total_payroll': salary_report['total_payroll'],
                        'employee_count': len(salary_report['employees']),
                        'avg_salary': salary_report['total_payroll'] / len(salary_report['employees']) if salary_report['employees'] else 0
                    })
            
            # Рассчитываем изменения
            if len(trends_data) >= 2:
                current = trends_data[0]
                previous = trends_data[1]
                
                payroll_change = current['total_payroll'] - previous['total_payroll']
                payroll_change_percent = (payroll_change / previous['total_payroll'] * 100) if previous['total_payroll'] > 0 else 0
                
                avg_salary_change = current['avg_salary'] - previous['avg_salary']
                avg_salary_change_percent = (avg_salary_change / previous['avg_salary'] * 100) if previous['avg_salary'] > 0 else 0
            else:
                payroll_change = 0
                payroll_change_percent = 0
                avg_salary_change = 0
                avg_salary_change_percent = 0
            
            return {
                'status': 'success',
                'trends_data': trends_data,
                'payroll_change': payroll_change,
                'payroll_change_percent': payroll_change_percent,
                'avg_salary_change': avg_salary_change,
                'avg_salary_change_percent': avg_salary_change_percent,
                'trend_direction': '📈 Рост' if payroll_change > 0 else '📉 Снижение' if payroll_change < 0 else '➡️ Стабильно'
            }
            
        except Exception as e:
            return {'status': 'error', 'message': f'Ошибка анализа трендов: {e}'}
    
    def get_salary_summary(self) -> str:
        """Возвращает сводку по зарплатам в текстовом формате"""
        try:
            # Получаем текущий месяц
            now = datetime.now()
            salary_report = self.get_detailed_salary_report(now.month, now.year)
            efficiency = self.get_efficiency_analysis(now.month, now.year)
            trends = self.get_salary_trends(3)
            
            result = "💰 **УПРАВЛЕНИЕ ЗАРПЛАТАМИ**\n\n"
            
            if salary_report['status'] == 'success':
                result += f"📅 **Зарплаты за {salary_report['month']}**\n"
                result += f"💵 Общий фонд: {salary_report['total_payroll']:,.0f} тенге\n"
                result += f"👥 Сотрудников: {len(salary_report['employees'])}\n"
                result += f"📊 Средняя зарплата: {salary_report['total_payroll'] / len(salary_report['employees']):,.0f} тенге\n\n"
                
                # Топ-3 по зарплатам
                top_employees = sorted(
                    salary_report['employees'].items(),
                    key=lambda x: x[1]['total_salary'],
                    reverse=True
                )[:3]
                
                result += "🏆 **Топ-3 по зарплатам:**\n"
                for i, (emp, data) in enumerate(top_employees, 1):
                    result += f"{i}. {emp}: {data['total_salary']:,.0f} тенге\n"
                
                result += "\n"
            
            if efficiency['status'] == 'success' and efficiency['top_performer']:
                top_performer = efficiency['top_performer']
                result += f"🌟 **Лучший по эффективности:**\n"
                result += f"👤 {top_performer[0]}: ROI {top_performer[1]['roi_percent']:.1f}%\n"
                result += f"📈 Продаж на тенге зарплаты: {top_performer[1]['sales_per_salary']:.1f}\n\n"
            
            if trends['status'] == 'success':
                result += f"📊 **Тренд зарплат:** {trends['trend_direction']}\n"
                if trends['payroll_change'] != 0:
                    result += f"💰 Изменение: {trends['payroll_change']:+,.0f} тенге ({trends['payroll_change_percent']:+.1f}%)\n"
            
            return result
            
        except Exception as e:
            return f"❌ Ошибка создания сводки: {e}"

# Пример использования
if __name__ == "__main__":
    manager = SalaryManagement("Alseit.xlsx")
    
    # Получаем детальную ведомость
    report = manager.get_detailed_salary_report()
    print(report)
    
    # Получаем сводку
    summary = manager.get_salary_summary()
    print(summary)
