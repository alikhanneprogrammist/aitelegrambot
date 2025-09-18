@echo off
REM Скрипт для переименования сотрудников в Windows
REM Использование: rename_employee.bat "старое_имя" "новое_имя" [--dry-run]

if "%~1"=="" (
    echo ❌ Неверное количество аргументов!
    echo.
    echo 📖 ИСПОЛЬЗОВАНИЕ:
    echo   rename_employee.bat "старое_имя" "новое_имя" [--dry-run]
    echo.
    echo 📝 ПРИМЕРЫ:
    echo   rename_employee.bat "Иван" "Иван Петров"
    echo   rename_employee.bat "Анна" "Анна Иванова" --dry-run
    echo   rename_employee.bat "Менеджер1" "Алексей"
    echo.
    echo 💡 ОПЦИИ:
    echo   --dry-run    - только показать что будет изменено, не сохранять
    echo   --help       - показать справку
    pause
    exit /b 1
)

if "%~1"=="--help" (
    echo 🔧 СКРИПТ ПЕРЕИМЕНОВАНИЯ СОТРУДНИКОВ
    echo ================================================
    echo.
    echo 📖 ИСПОЛЬЗОВАНИЕ:
    echo   rename_employee.bat "старое_имя" "новое_имя" [--dry-run]
    echo.
    echo 📝 ПРИМЕРЫ:
    echo   rename_employee.bat "Иван" "Иван Петров"
    echo   rename_employee.bat "Анна" "Анна Иванова" --dry-run
    echo   rename_employee.bat "Менеджер1" "Алексей"
    echo.
    echo 💡 ОПЦИИ:
    echo   --dry-run    - только показать что будет изменено, не сохранять
    echo   --help       - показать эту справку
    echo.
    echo 📁 ФАЙЛЫ:
    echo   • Alseit.xlsx (листы: продажи, зарплата)
    echo   • expenses.xlsx (листы: personal, office)
    echo.
    echo ⚠️  ВАЖНО:
    echo   • Имена в кавычках если содержат пробелы
    echo   • Сначала используйте --dry-run для проверки
    echo   • Создайте резервную копию файлов перед изменением
    pause
    exit /b 0
)

echo 🔧 СКРИПТ ПЕРЕИМЕНОВАНИЯ СОТРУДНИКОВ
echo ================================================
echo 📝 Старое имя: %~1
echo 📝 Новое имя: %~2
echo 🔍 Режим: %~3
echo.

python rename_employee.py %*

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo ❌ Ошибка выполнения скрипта
    echo 💡 Убедитесь, что Python установлен и файлы доступны
)

echo.
pause
