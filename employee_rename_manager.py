"""
Менеджер для переименования сотрудников в Excel файлах
"""

import pandas as pd
import os
from typing import Dict, List, Tuple, Optional
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmployeeRenameManager:
    """
    Класс для управления переименованием сотрудников в Excel файлах
    """
    
    def __init__(self, excel_file_path: str = None, expenses_file_path: str = None):
        """
        Инициализация менеджера переименования
        
        Args:
            excel_file_path: Путь к основному Excel файлу (Alseit.xlsx)
            expenses_file_path: Путь к файлу расходов (expenses.xlsx)
        """
        if excel_file_path is None:
            excel_file_path = os.path.join(os.path.dirname(__file__), "Alseit.xlsx")
        if expenses_file_path is None:
            expenses_file_path = os.path.join(os.path.dirname(__file__), "expenses.xlsx")
            
        self.excel_file_path = excel_file_path
        self.expenses_file_path = expenses_file_path
        
    def get_all_employee_names(self) -> Dict[str, List[str]]:
        """
        Получить все имена сотрудников из всех файлов
        
        Returns:
            Dict с именами сотрудников по файлам и листам
        """
        employees = {
            'Alseit.xlsx': {
                'продажи': [],
                'зарплата': []
            },
            'expenses.xlsx': {
                'personal': [],
                'office': []
            }
        }
        
        try:
            # Читаем Alseit.xlsx
            if os.path.exists(self.excel_file_path):
                # Лист продажи - колонка manager
                try:
                    sales_df = pd.read_excel(self.excel_file_path, sheet_name="продажи")
                    if 'manager' in sales_df.columns:
                        managers = sales_df['manager'].dropna().unique().tolist()
                        employees['Alseit.xlsx']['продажи'] = [str(m) for m in managers if str(m).strip()]
                except Exception as e:
                    logger.warning(f"Ошибка чтения листа 'продажи': {e}")
                
                # Лист зарплата - колонки менеджеров
                try:
                    salary_df = pd.read_excel(self.excel_file_path, sheet_name="зарплата")
                    exclude_cols = ['date', 'order', 'developer', 'employee ROP', 'assistant', 'assistant 2', 'supplier manager']
                    manager_cols = [col for col in salary_df.columns if col not in exclude_cols]
                    employees['Alseit.xlsx']['зарплата'] = manager_cols
                except Exception as e:
                    logger.warning(f"Ошибка чтения листа 'зарплата': {e}")
            
            # Читаем expenses.xlsx
            if os.path.exists(self.expenses_file_path):
                for sheet_name in ['personal', 'office']:
                    try:
                        df = pd.read_excel(self.expenses_file_path, sheet_name=sheet_name)
                        if 'employee' in df.columns:
                            emp_names = df['employee'].dropna().unique().tolist()
                            employees['expenses.xlsx'][sheet_name] = [str(e) for e in emp_names if str(e).strip()]
                    except Exception as e:
                        logger.warning(f"Ошибка чтения листа '{sheet_name}': {e}")
                        
        except Exception as e:
            logger.error(f"Ошибка получения имен сотрудников: {e}")
            
        return employees
    
    def rename_employee(self, old_name: str, new_name: str, dry_run: bool = False) -> Dict[str, bool]:
        """
        Переименовать сотрудника во всех файлах
        
        Args:
            old_name: Старое имя сотрудника
            new_name: Новое имя сотрудника
            dry_run: Если True, только проверить что будет изменено, не сохранять
            
        Returns:
            Dict с результатами переименования по файлам
        """
        results = {
            'Alseit.xlsx': {'продажи': False, 'зарплата': False},
            'expenses.xlsx': {'personal': False, 'office': False}
        }
        
        try:
            # Обрабатываем Alseit.xlsx
            if os.path.exists(self.excel_file_path):
                # Лист продажи
                try:
                    sales_df = pd.read_excel(self.excel_file_path, sheet_name="продажи")
                    if 'manager' in sales_df.columns:
                        old_count = (sales_df['manager'] == old_name).sum()
                        if old_count > 0:
                            if not dry_run:
                                sales_df['manager'] = sales_df['manager'].replace(old_name, new_name)
                                # Сохраняем изменения
                                with pd.ExcelWriter(self.excel_file_path, mode='a', if_sheet_exists='replace') as writer:
                                    sales_df.to_excel(writer, sheet_name='продажи', index=False)
                            results['Alseit.xlsx']['продажи'] = True
                            logger.info(f"Найдено {old_count} записей в листе 'продажи' для переименования")
                except Exception as e:
                    logger.error(f"Ошибка переименования в листе 'продажи': {e}")
                
                # Лист зарплата
                try:
                    salary_df = pd.read_excel(self.excel_file_path, sheet_name="зарплата")
                    if old_name in salary_df.columns:
                        if not dry_run:
                            # Переименовываем колонку
                            salary_df = salary_df.rename(columns={old_name: new_name})
                            # Сохраняем изменения
                            with pd.ExcelWriter(self.excel_file_path, mode='a', if_sheet_exists='replace') as writer:
                                salary_df.to_excel(writer, sheet_name='зарплата', index=False)
                        results['Alseit.xlsx']['зарплата'] = True
                        logger.info(f"Переименована колонка в листе 'зарплата'")
                except Exception as e:
                    logger.error(f"Ошибка переименования в листе 'зарплата': {e}")
            
            # Обрабатываем expenses.xlsx
            if os.path.exists(self.expenses_file_path):
                for sheet_name in ['personal', 'office']:
                    try:
                        df = pd.read_excel(self.expenses_file_path, sheet_name=sheet_name)
                        if 'employee' in df.columns:
                            old_count = (df['employee'] == old_name).sum()
                            if old_count > 0:
                                if not dry_run:
                                    df['employee'] = df['employee'].replace(old_name, new_name)
                                    # Сохраняем изменения
                                    with pd.ExcelWriter(self.expenses_file_path, mode='a', if_sheet_exists='replace') as writer:
                                        df.to_excel(writer, sheet_name=sheet_name, index=False)
                                results['expenses.xlsx'][sheet_name] = True
                                logger.info(f"Найдено {old_count} записей в листе '{sheet_name}' для переименования")
                    except Exception as e:
                        logger.error(f"Ошибка переименования в листе '{sheet_name}': {e}")
                        
        except Exception as e:
            logger.error(f"Ошибка переименования сотрудника: {e}")
            
        return results
    
    def get_rename_preview(self, old_name: str, new_name: str) -> Dict[str, int]:
        """
        Получить предварительный просмотр изменений
        
        Args:
            old_name: Старое имя
            new_name: Новое имя
            
        Returns:
            Dict с количеством изменений по файлам
        """
        preview = {
            'Alseit.xlsx': {'продажи': 0, 'зарплата': 0},
            'expenses.xlsx': {'personal': 0, 'office': 0}
        }
        
        try:
            # Alseit.xlsx - продажи
            if os.path.exists(self.excel_file_path):
                try:
                    sales_df = pd.read_excel(self.excel_file_path, sheet_name="продажи")
                    if 'manager' in sales_df.columns:
                        preview['Alseit.xlsx']['продажи'] = (sales_df['manager'] == old_name).sum()
                except:
                    pass
                
                # Alseit.xlsx - зарплата
                try:
                    salary_df = pd.read_excel(self.excel_file_path, sheet_name="зарплата")
                    preview['Alseit.xlsx']['зарплата'] = 1 if old_name in salary_df.columns else 0
                except:
                    pass
            
            # expenses.xlsx
            if os.path.exists(self.expenses_file_path):
                for sheet_name in ['personal', 'office']:
                    try:
                        df = pd.read_excel(self.expenses_file_path, sheet_name=sheet_name)
                        if 'employee' in df.columns:
                            preview['expenses.xlsx'][sheet_name] = (df['employee'] == old_name).sum()
                    except:
                        pass
                        
        except Exception as e:
            logger.error(f"Ошибка получения предварительного просмотра: {e}")
            
        return preview
    
    def validate_rename(self, old_name: str, new_name: str) -> Tuple[bool, str]:
        """
        Проверить валидность переименования
        
        Args:
            old_name: Старое имя
            new_name: Новое имя
            
        Returns:
            Tuple (is_valid, error_message)
        """
        if not old_name or not new_name:
            return False, "Имена не могут быть пустыми"
            
        if old_name.strip() == new_name.strip():
            return False, "Старое и новое имя одинаковые"
            
        if len(new_name.strip()) < 2:
            return False, "Новое имя должно содержать минимум 2 символа"
            
        # Проверяем, что старое имя существует
        employees = self.get_all_employee_names()
        old_name_found = False
        for file_data in employees.values():
            for sheet_data in file_data.values():
                if old_name in sheet_data:
                    old_name_found = True
                    break
            if old_name_found:
                break
                
        if not old_name_found:
            return False, f"Сотрудник '{old_name}' не найден в файлах"
            
        return True, ""

def main():
    """
    Основная функция для использования из терминала
    """
    import sys
    
    if len(sys.argv) < 3:
        print("Использование: python employee_rename_manager.py <старое_имя> <новое_имя> [--dry-run]")
        print("Пример: python employee_rename_manager.py 'Иван' 'Иван Петров'")
        print("Пример: python employee_rename_manager.py 'Иван' 'Иван Петров' --dry-run")
        sys.exit(1)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    dry_run = '--dry-run' in sys.argv
    
    manager = EmployeeRenameManager()
    
    # Валидация
    is_valid, error_msg = manager.validate_rename(old_name, new_name)
    if not is_valid:
        print(f"❌ Ошибка: {error_msg}")
        sys.exit(1)
    
    # Предварительный просмотр
    preview = manager.get_rename_preview(old_name, new_name)
    print(f"📋 Предварительный просмотр переименования '{old_name}' → '{new_name}':")
    
    total_changes = 0
    for file_name, sheets in preview.items():
        for sheet_name, count in sheets.items():
            if count > 0:
                print(f"  📄 {file_name} ({sheet_name}): {count} изменений")
                total_changes += count
    
    if total_changes == 0:
        print("  ℹ️ Изменений не найдено")
        sys.exit(0)
    
    if dry_run:
        print(f"\n🔍 Режим предварительного просмотра - изменения не будут сохранены")
        sys.exit(0)
    
    # Подтверждение
    confirm = input(f"\n❓ Выполнить переименование? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', 'да', 'д']:
        print("❌ Операция отменена")
        sys.exit(0)
    
    # Выполнение переименования
    print(f"\n🔄 Выполняю переименование...")
    results = manager.rename_employee(old_name, new_name, dry_run=False)
    
    # Результаты
    success_count = 0
    for file_name, sheets in results.items():
        for sheet_name, success in sheets.items():
            if success:
                print(f"✅ {file_name} ({sheet_name}): успешно")
                success_count += 1
            else:
                print(f"⚠️ {file_name} ({sheet_name}): пропущено")
    
    if success_count > 0:
        print(f"\n🎉 Переименование завершено! Изменено в {success_count} местах")
    else:
        print(f"\n❌ Переименование не выполнено")

if __name__ == "__main__":
    main()
