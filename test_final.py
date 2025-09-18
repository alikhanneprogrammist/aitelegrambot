#!/usr/bin/env python3
"""
Финальный тест для проверки создания заказов
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sales_folder.chatgpt_analyzer import ChatGPTAnalyzer
import pandas as pd

def test_create_order():
    """Тестируем создание заказа"""
    
    # Создаем экземпляр анализатора
    analyzer = ChatGPTAnalyzer()
    
    # Создаем тестовый Excel файл
    test_data = {
        'order': [1, 2, 3],
        'date': ['2025-01-01', '2025-01-02', '2025-01-03'],
        'client': ['Клиент1', 'Клиент2', 'Клиент3'],
        'boiler_name': ['alseit_25', 'alseit_30', 'alseit_40'],
        'quantity': [1, 2, 1],
        'price': [870000, 1940000, 1300000],
        'purchase': [566500, 1173000, 646500],
        'payment_method': ['карта', 'карта', 'карта'],
        'delivery': ['магазин', 'дом', 'магазин'],
        'accessories': ['', '', ''],
        'manager': ['Алибек', 'Алибек', 'Алибек'],
        'delivery_cost': [0, 55000, 0]
    }
    
    test_df = pd.DataFrame(test_data)
    test_file = 'test_orders.xlsx'
    
    # Создаем Excel файл с листом "продажи"
    with pd.ExcelWriter(test_file, engine='openpyxl') as writer:
        test_df.to_excel(writer, sheet_name='продажи', index=False)
    
    print("🧪 Тестируем создание заказа...")
    
    # Тестовая команда
    test_command = "Создай новый заказ balseit _20 доставка магазин менеджер Алибек"
    
    try:
        # Вызываем метод редактирования
        result = analyzer.edit_excel_data(test_file, test_command)
        
        print("📋 Результат:")
        print(result)
        
        # Проверяем, что файл обновился
        updated_df = pd.read_excel(test_file)
        print(f"\n📊 Записей в файле: {len(updated_df)}")
        print(f"📊 Последний заказ: {updated_df.iloc[-1]['order']}")
        
        # Удаляем тестовый файл
        os.remove(test_file)
        
        return "✅" in result
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        # Удаляем тестовый файл в случае ошибки
        if os.path.exists(test_file):
            os.remove(test_file)
        return False

if __name__ == "__main__":
    print("🚀 Запуск финального теста...")
    success = test_create_order()
    
    if success:
        print("\n✅ Тест прошел успешно!")
    else:
        print("\n❌ Тест не прошел")
    
    sys.exit(0 if success else 1)
