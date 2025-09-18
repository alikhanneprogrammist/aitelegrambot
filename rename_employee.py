#!/usr/bin/env python3
"""
Скрипт для переименования сотрудников через терминал
Использование: python rename_employee.py <старое_имя> <новое_имя> [--dry-run]
"""

import sys
import os
from employee_rename_manager import EmployeeRenameManager

def main():
    """Основная функция скрипта"""
    
    # Проверяем аргументы
    if len(sys.argv) < 3:
        print("❌ Неверное количество аргументов!")
        print("\n📖 ИСПОЛЬЗОВАНИЕ:")
        print("  python rename_employee.py <старое_имя> <новое_имя> [--dry-run]")
        print("\n📝 ПРИМЕРЫ:")
        print("  python rename_employee.py \"Иван\" \"Иван Петров\"")
        print("  python rename_employee.py \"Анна\" \"Анна Иванова\" --dry-run")
        print("  python rename_employee.py \"Менеджер1\" \"Алексей\"")
        print("\n💡 ОПЦИИ:")
        print("  --dry-run    - только показать что будет изменено, не сохранять")
        print("  --help       - показать эту справку")
        sys.exit(1)
    
    # Обработка --help
    if '--help' in sys.argv or '-h' in sys.argv:
        print("🔧 СКРИПТ ПЕРЕИМЕНОВАНИЯ СОТРУДНИКОВ")
        print("=" * 50)
        print("\n📖 ИСПОЛЬЗОВАНИЕ:")
        print("  python rename_employee.py <старое_имя> <новое_имя> [--dry-run]")
        print("\n📝 ПРИМЕРЫ:")
        print("  python rename_employee.py \"Иван\" \"Иван Петров\"")
        print("  python rename_employee.py \"Анна\" \"Анна Иванова\" --dry-run")
        print("  python rename_employee.py \"Менеджер1\" \"Алексей\"")
        print("\n💡 ОПЦИИ:")
        print("  --dry-run    - только показать что будет изменено, не сохранять")
        print("  --help, -h   - показать эту справку")
        print("\n📁 ФАЙЛЫ:")
        print("  • Alseit.xlsx (листы: продажи, зарплата)")
        print("  • expenses.xlsx (листы: personal, office)")
        print("\n⚠️  ВАЖНО:")
        print("  • Имена в кавычках если содержат пробелы")
        print("  • Сначала используйте --dry-run для проверки")
        print("  • Создайте резервную копию файлов перед изменением")
        sys.exit(0)
    
    old_name = sys.argv[1]
    new_name = sys.argv[2]
    dry_run = '--dry-run' in sys.argv
    
    print("🔧 СКРИПТ ПЕРЕИМЕНОВАНИЯ СОТРУДНИКОВ")
    print("=" * 50)
    print(f"📝 Старое имя: '{old_name}'")
    print(f"📝 Новое имя: '{new_name}'")
    print(f"🔍 Режим: {'предварительный просмотр' if dry_run else 'выполнение'}")
    print()
    
    # Инициализируем менеджер
    try:
        manager = EmployeeRenameManager()
    except Exception as e:
        print(f"❌ Ошибка инициализации: {e}")
        sys.exit(1)
    
    # Валидация
    print("🔍 Проверяю валидность...")
    is_valid, error_msg = manager.validate_rename(old_name, new_name)
    if not is_valid:
        print(f"❌ Ошибка валидации: {error_msg}")
        sys.exit(1)
    print("✅ Валидация прошла успешно")
    print()
    
    # Предварительный просмотр
    print("📋 Получаю предварительный просмотр...")
    preview = manager.get_rename_preview(old_name, new_name)
    
    print("📊 НАЙДЕННЫЕ ИЗМЕНЕНИЯ:")
    total_changes = 0
    changes_found = False
    
    for file_name, sheets in preview.items():
        file_changes = 0
        for sheet_name, count in sheets.items():
            if count > 0:
                file_changes += count
                total_changes += count
                changes_found = True
        
        if file_changes > 0:
            print(f"  📄 {file_name}: {file_changes} изменений")
            for sheet_name, count in sheets.items():
                if count > 0:
                    print(f"    📋 {sheet_name}: {count} записей")
    
    if not changes_found:
        print("  ℹ️ Изменений не найдено")
        print("\n💡 Возможные причины:")
        print("  • Сотрудник с таким именем не найден")
        print("  • Имя написано с ошибкой")
        print("  • Сотрудник уже переименован")
        print("\n🔍 Для просмотра всех сотрудников используйте:")
        print("  python -c \"from employee_rename_manager import EmployeeRenameManager; print(EmployeeRenameManager().get_all_employee_names())\"")
        sys.exit(0)
    
    print(f"\n📈 ИТОГО: {total_changes} изменений")
    
    if dry_run:
        print(f"\n🔍 РЕЖИМ ПРЕДВАРИТЕЛЬНОГО ПРОСМОТРА")
        print("   Изменения НЕ будут сохранены")
        print("   Для выполнения используйте команду без --dry-run")
        sys.exit(0)
    
    # Подтверждение
    print(f"\n❓ ВЫПОЛНИТЬ ПЕРЕИМЕНОВАНИЕ?")
    print(f"   '{old_name}' → '{new_name}'")
    print(f"   {total_changes} изменений в файлах")
    
    while True:
        confirm = input("\n   Введите 'да' для подтверждения или 'нет' для отмены: ").strip().lower()
        if confirm in ['да', 'д', 'yes', 'y']:
            break
        elif confirm in ['нет', 'н', 'no', 'n']:
            print("❌ Операция отменена пользователем")
            sys.exit(0)
        else:
            print("⚠️ Пожалуйста, введите 'да' или 'нет'")
    
    # Выполнение переименования
    print(f"\n🔄 Выполняю переименование...")
    try:
        results = manager.rename_employee(old_name, new_name, dry_run=False)
        
        # Результаты
        print(f"\n📊 РЕЗУЛЬТАТЫ:")
        success_count = 0
        for file_name, sheets in results.items():
            file_success = False
            for sheet_name, success in sheets.items():
                if success:
                    file_success = True
                    success_count += 1
            
            if file_success:
                print(f"  ✅ {file_name}: успешно")
            else:
                print(f"  ⚠️ {file_name}: пропущено")
        
        if success_count > 0:
            print(f"\n🎉 ПЕРЕИМЕНОВАНИЕ ЗАВЕРШЕНО!")
            print(f"   Изменено в {success_count} местах")
            print(f"   '{old_name}' → '{new_name}'")
        else:
            print(f"\n❌ ПЕРЕИМЕНОВАНИЕ НЕ ВЫПОЛНЕНО")
            print("   Изменения не были внесены")
            
    except Exception as e:
        print(f"\n❌ ОШИБКА ВЫПОЛНЕНИЯ: {e}")
        print("   Проверьте права доступа к файлам")
        print("   Убедитесь, что файлы не открыты в Excel")
        sys.exit(1)

if __name__ == "__main__":
    main()
