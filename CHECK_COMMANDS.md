# Команды для проверки кода

## Установка зависимостей

```bash
# Установка основных зависимостей
pip install -r requirements.txt

# Установка зависимостей для тестирования
pip install pytest pytest-cov flake8 mypy black

# Установка зависимостей для проверки безопасности
pip install bandit safety
```

## Запуск тестов

```bash
# Запуск всех тестов
python -m pytest tests/ -v

# Запуск тестов с покрытием кода
python -m pytest tests/ --cov=. --cov-report=html

# Запуск только unit тестов
python -m pytest tests/ -m unit -v

# Запуск только интеграционных тестов
python -m pytest tests/ -m integration -v
```

## Проверка стиля кода

```bash
# Проверка с flake8
flake8 . --max-line-length=88 --extend-ignore=E203,W503

# Автоматическое исправление с black
black . --line-length=88

# Проверка типов с mypy
mypy . --ignore-missing-imports
```

## Проверка безопасности

```bash
# Проверка безопасности с bandit
bandit -r . -f json -o bandit-report.json

# Проверка уязвимостей в зависимостях
safety check --json --output safety-report.json
```

## Проверка производительности

```bash
# Профилирование с cProfile
python -m cProfile -s cumulative bot.py

# Проверка памяти с memory_profiler
pip install memory_profiler
python -m memory_profiler bot.py
```

## Полная проверка

```bash
# Создание скрипта для полной проверки
cat > check_all.sh << 'EOF'
#!/bin/bash
echo "🔍 Запуск полной проверки кода..."

echo "📦 Установка зависимостей..."
pip install -r requirements.txt
pip install pytest pytest-cov flake8 mypy black bandit safety

echo "🧪 Запуск тестов..."
python -m pytest tests/ -v --cov=. --cov-report=html

echo "🎨 Проверка стиля кода..."
flake8 . --max-line-length=88 --extend-ignore=E203,W503
black . --line-length=88 --check

echo "🔒 Проверка безопасности..."
bandit -r . -f json -o bandit-report.json
safety check --json --output safety-report.json

echo "✅ Проверка завершена!"
echo "📊 Отчеты:"
echo "  - Покрытие кода: htmlcov/index.html"
echo "  - Безопасность: bandit-report.json, safety-report.json"
EOF

chmod +x check_all.sh
./check_all.sh
```

## Ручная проверка

### 1. Синтаксические ошибки
```bash
python -m py_compile bot.py
python -m py_compile utils.py
python -m py_compile config.py
```

### 2. Импорты
```bash
python -c "import bot; print('bot.py - OK')"
python -c "import utils; print('utils.py - OK')"
python -c "import config; print('config.py - OK')"
```

### 3. Тестирование основных функций
```bash
python -c "
from utils import DataCache, find_column, clean_numeric_data
import pandas as pd

# Тест кэша
cache = DataCache()
print('✅ DataCache работает')

# Тест поиска колонок
df = pd.DataFrame({'price': [1, 2, 3], 'manager': ['A', 'B', 'C']})
col = find_column(df, 'price')
print(f'✅ find_column работает: {col}')

# Тест очистки данных
cleaned = clean_numeric_data(df, 'price')
print(f'✅ clean_numeric_data работает: {len(cleaned)} записей')
"
```

## Рекомендации по улучшению

1. **Добавить больше тестов** для edge cases
2. **Настроить CI/CD** для автоматической проверки
3. **Добавить pre-commit hooks** для проверки перед коммитом
4. **Настроить мониторинг** производительности в продакшене
5. **Добавить логирование** ошибок в файл
6. **Настроить ротацию логов** для предотвращения переполнения диска

