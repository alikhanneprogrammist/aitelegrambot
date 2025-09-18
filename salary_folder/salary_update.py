# salary_update.py
import pandas as pd
import os
from dotenv import load_dotenv

load_dotenv()
excel_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), os.getenv("EXCEL_FILE_NAME", "Alseit.xlsx"))

# Словарь с ценами котлов и закупочными ценами
BOILER_PRICES = {
    'alseit_25': {'price': 870000, 'purchase': 566500},
    'alseit_30': {'price': 970000, 'purchase': 586500},
    'alseit_40': {'price': 1300000, 'purchase': 646500},
    'alseit_50': {'price': 1400000, 'purchase': 696500},
    'alseit_60': {'price': 1500000, 'purchase': 746500},
    'alseit_70': {'price': 1600000, 'purchase': 796500},
    'alseit_80': {'price': 1800000, 'purchase': 896500},
    'alseit_90': {'price': 2000000, 'purchase': 946500},
    'alseit_100': {'price': 2400000, 'purchase': 1246500},
    'alseit_120': {'price': 3000000, 'purchase': 1546500},
    'стандарт_16': {'price': 790000, 'purchase': 496500},
    'стандарт_20': {'price': 830000, 'purchase': 521500},
    'мини_20': {'price': 750000, 'purchase': 456500},
    'мини_16': {'price': 650000, 'purchase': 396500},
    'мини_12': {'price': 570000, 'purchase': 331500},
    'balseit_15': {'price': 690000, 'purchase': 321000},
    'balseit_20': {'price': 790000, 'purchase': 430000}
}

# Котлы с вычетом 50,000 (мини 12-20 и alseit 25-30)
LOW_DEDUCTION_BOILERS = ['мини_12', 'мини_16', 'мини_20', 'alseit_25', 'alseit_30']
LOW_DEDUCTION_AMOUNT = 50000
HIGH_DEDUCTION_AMOUNT = 100000

# Процентные ставки
MANAGER_BONUS_RATE = 0.05  # 5% сотруднику
ROP_BONUS_RATE = 0.01      # 1% РОП
BANK_TAX_RATE = 0.12       # 12% налог при оплате через банк

def calculate_boiler_bonus(boiler_name, payment_method, delivery_amount, accessories=0, quantity=1):
    """
    Рассчитывает бонус для котла по новой логике:
    - Бонус менеджера: (price - доставка) * 5%
      - мини 12-20 и alseit 25-30: доставка = 50,000
      - остальные: доставка = 100,000
      - если наличными: (price - 4700) * 5%
    - Чистая прибыль: price - 12%(если банк) - 4% налог - доставка - бонус менеджера - purchase
    """
    if boiler_name not in BOILER_PRICES:
        return 0, 0, 0  # manager_bonus, rop_bonus, profit
    
    boiler_data = BOILER_PRICES[boiler_name]
    price = boiler_data['price']
    purchase = boiler_data['purchase']
    
    if price == 0:  # Для elbrus_100 без цены
        return 0, 0, 0
    
    # Общая стоимость
    total_price = price * quantity
    total_purchase = purchase * quantity
    
    # Определяем сумму доставки для расчета бонусов
    # ВСЕГДА используем фиксированные значения по типу котла (независимо от способа оплаты)
    if boiler_name in LOW_DEDUCTION_BOILERS:
        delivery_for_bonus = LOW_DEDUCTION_AMOUNT  # 50,000 для мини 12-20 и alseit 25-30
    else:
        delivery_for_bonus = HIGH_DEDUCTION_AMOUNT  # 100,000 для остальных
    
    # Рассчитываем бонус менеджера
    manager_bonus = (total_price - delivery_for_bonus) * MANAGER_BONUS_RATE
    
    # Рассчитываем ROP бонус (1% от той же базы)
    rop_bonus = (total_price - delivery_for_bonus) * ROP_BONUS_RATE
    
    # Рассчитываем чистую прибыль
    # price - 12%(если банк) - 4% налог - бонус менеджера - purchase - аксессуары
    # Доставка уже учтена в фиксированных суммах (50,000/100,000) для бонусов
    profit = total_price
    
    # Вычитаем 12% если оплата через банк
    if payment_method in ['банк', 'kaspi_pay', 'kaspi_magazine']:
        bank_tax = total_price * BANK_TAX_RATE
        profit -= bank_tax
    
    # Вычитаем 4% налог
    tax_4_percent = total_price * 0.04
    profit -= tax_4_percent
    
    # НЕ вычитаем доставку - она уже учтена в фиксированных суммах для бонусов
    
    # Вычитаем бонус менеджера
    profit -= manager_bonus
    
    # Вычитаем закупочную стоимость
    profit -= total_purchase
    
    # Вычитаем аксессуары
    profit -= accessories
    
    return manager_bonus, rop_bonus, profit

def update_salary():
    sales = pd.read_excel(excel_path, sheet_name="продажи")
    salary = pd.read_excel(excel_path, sheet_name="зарплата")

    # === 2. Новые расчеты с учетом котлов ===
    delivery_pay = float(os.getenv("DELIVERY_PAY", "55000"))
    delivery_shop = float(os.getenv("DELIVERY_SHOP", "4700"))
    
    # Создаем временные колонки для расчетов (не сохраняем в Excel)
    sales['temp_manager_bonus'] = 0.0
    sales['temp_salary_rop'] = 0.0
    sales['temp_profit'] = 0.0
    
    # Рассчитываем бонусы для каждой продажи
    for idx, row in sales.iterrows():
        boiler_name = row.get('boiler_name', '')
        payment_method = row.get('payment_method', 'наличные')
        quantity = row.get('quantity', 1)
        delivery = row.get('delivery', '')
        accessories = row.get('accessories', 0)
        
        # Пропускаем строки без названия котла
        if pd.isna(boiler_name) or boiler_name == '':
            continue
            
        # Убираем пробелы в начале и конце
        boiler_name = str(boiler_name).strip()
            
        # Обрабатываем NaN в payment_method
        if pd.isna(payment_method):
            payment_method = 'наличные'
        else:
            payment_str = str(payment_method).strip().lower()
            if payment_str in ['нал', 'наличные', 'наличка', 'cash']:
                payment_method = 'наличные'
            elif payment_str in ['банк', 'банковский', 'карта', 'bank', 'card']:
                payment_method = 'банк'
            else:
                payment_method = 'наличные'  # По умолчанию
            
        # Обрабатываем NaN в quantity
        if pd.isna(quantity):
            quantity = 1
            
        # Обрабатываем delivery - определяем сумму доставки
        delivery_amount = 0
        if not pd.isna(delivery) and delivery != '':
            delivery_str = str(delivery).strip().lower()
            if delivery_str == 'пэй':
                delivery_amount = delivery_pay  # 55,000
            elif delivery_str == 'магазин':
                delivery_amount = delivery_shop  # 4,700
            else:
                # Пытаемся извлечь число из строки
                try:
                    delivery_amount = float(delivery_str)
                except:
                    delivery_amount = 0
        
        # Обрабатываем NaN в accessories
        if pd.isna(accessories):
            accessories = 0
        else:
            try:
                accessories = float(accessories)
            except:
                accessories = 0
        
        manager_bonus, rop_bonus, profit = calculate_boiler_bonus(
            boiler_name, payment_method, delivery_amount, accessories, quantity
        )
        
        sales.loc[idx, 'temp_manager_bonus'] = manager_bonus
        sales.loc[idx, 'temp_salary_rop'] = rop_bonus
        sales.loc[idx, 'temp_profit'] = profit
        sales.loc[idx, 'delivery_cost'] = delivery_amount
    
    # Стоимость доставки теперь рассчитывается в цикле выше

    # === 3. Готовим продажи для зарплаты ===
    sales['date'] = pd.to_datetime(sales['date'], format='%d.%m.%Y', errors='coerce')

    # Автоматически определяем колонки менеджеров из листа зарплаты
    # Исключаем служебные колонки
    exclude_cols = ['date', 'order', 'developer', 'employee ROP', 'assistant', 'assistant 2', 'supplier manager']
    manager_cols = [c for c in salary.columns if c not in exclude_cols]
    
    print(f"🔍 Найденные колонки менеджеров: {manager_cols}")

    # Создаем словарь для группировки бонусов по дате и заказу
    bonus_dict = {}
    
    for idx, row in sales.iterrows():
        # Пропускаем только строки без названия котла
        if pd.isna(row['boiler_name']) or row['boiler_name'] == '':
            continue
            
        date = row['date']
        order = row['order']
        key = (date, order)
        
        if key not in bonus_dict:
            bonus_dict[key] = {
                'date': date,
                'order': order,
                'employee ROP': 0,
                'managers': {}
            }
        
        # Добавляем ROP бонус
        bonus_dict[key]['employee ROP'] += row['temp_salary_rop']
        
        # Добавляем бонус менеджера - проверяем все колонки менеджеров
        manager_name = row['manager']
        if manager_name in manager_cols:
            if manager_name not in bonus_dict[key]['managers']:
                bonus_dict[key]['managers'][manager_name] = 0
            bonus_dict[key]['managers'][manager_name] += row['temp_manager_bonus']
        else:
            # Если менеджер не найден в колонках, выводим предупреждение
            print(f"⚠️ Менеджер '{manager_name}' не найден в колонках зарплаты")
        

    # Создаем строки для зарплаты
    rows = []
    for key, data in bonus_dict.items():
        new_row = {col: 0 for col in salary.columns}
        new_row['date'] = data['date']
        new_row['order'] = data['order']
        new_row['employee ROP'] = data['employee ROP']
        
        # Добавляем бонусы менеджеров
        for manager, bonus in data['managers'].items():
            new_row[manager] = bonus
            
        rows.append(new_row)

    sales_salary = pd.DataFrame(rows)

    # === 4. Склеиваем: оклад + продажи ===
    salary_oklad = salary.iloc[[0]].copy()
    salary_final = pd.concat([salary_oklad, sales_salary], ignore_index=True)

    # === 5. Создаем сводку по бонусам ===
    bonus_summary = []
    
    # Добавляем ROP бонусы (оклад + бонусы от продаж)
    rop_oklad = salary_oklad['employee ROP'].iloc[0] if len(salary_oklad) > 0 else 0
    total_rop_bonus = sales_salary['employee ROP'].sum()
    total_rop_salary = rop_oklad + total_rop_bonus
    bonus_summary.append({
        'Тип': 'ROP сотрудники',
        'Сумма': total_rop_salary
    })
    
    # Добавляем оклады для разработчиков и ассистентов (только оклады, без бонусов)
    fixed_salary_cols = ['developer', 'assistant', 'assistant 2', 'supplier manager']
    for col in fixed_salary_cols:
        if col in salary_oklad.columns:
            oklad = salary_oklad[col].iloc[0] if len(salary_oklad) > 0 else 0
            if oklad > 0:
                bonus_summary.append({
                    'Тип': col,
                    'Сумма': oklad
                })
    
    # Добавляем бонусы менеджеров (оклад + бонусы от продаж)
    for col in manager_cols:
        if col in sales_salary.columns:
            # Оклад из первой строки
            oklad = salary_oklad[col].iloc[0] if len(salary_oklad) > 0 and col in salary_oklad.columns else 0
            # Бонусы от продаж
            bonus_from_sales = sales_salary[col].sum()
            # Общая сумма
            total_salary = oklad + bonus_from_sales
            
            if total_salary > 0:
                bonus_summary.append({
                    'Тип': col,
                    'Сумма': total_salary
                })
    
    # Добавляем общую сумму
    total_all_salaries = sum([item['Сумма'] for item in bonus_summary])
    bonus_summary.append({
        'Тип': 'ОБЩАЯ СУММА',
        'Сумма': total_all_salaries
    })
    
    bonus_summary_df = pd.DataFrame(bonus_summary)

    # === 6. Сохраняем ===
    # Читаем все существующие листы
    try:
        existing_sheets = {}
        xl_file = pd.ExcelFile(excel_path)
        for sheet_name in xl_file.sheet_names:
            if sheet_name not in ["продажи", "зарплата", "сводка_бонусов"]:
                existing_sheets[sheet_name] = pd.read_excel(excel_path, sheet_name=sheet_name)
    except:
        existing_sheets = {}
    
    # Удаляем только временные колонки перед сохранением
    # delivery_cost теперь заполняется автоматически и сохраняется
    columns_to_drop = ['temp_manager_bonus', 'temp_salary_rop', 'temp_profit']
    sales_clean = sales.drop(columns=columns_to_drop, errors='ignore')
    
    # Форматируем даты как строки для правильного отображения (день.месяц.год)
    sales_clean['date'] = pd.to_datetime(sales_clean['date'], format='%d.%m.%Y', errors='coerce').dt.strftime('%d.%m.%Y')
    salary_final['date'] = pd.to_datetime(salary_final['date'], format='%d.%m.%Y', errors='coerce').dt.strftime('%d.%m.%Y')
    
    # Сохраняем все листы
    with pd.ExcelWriter(excel_path, engine="openpyxl") as writer:
        # Сохраняем данные продаж БЕЗ колонок бонусов
        sales_clean.to_excel(writer, sheet_name="продажи", index=False)
        # Сохраняем зарплату с бонусами
        salary_final.to_excel(writer, sheet_name="зарплата", index=False)
        # Сохраняем сводку бонусов
        bonus_summary_df.to_excel(writer, sheet_name="сводка_бонусов", index=False)
        # Сохраняем остальные листы
        for sheet_name, df in existing_sheets.items():
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    # === 7. Формируем итоговое сообщение ===
    result_message = "✅ Salary обновлена: оклады + продажи по дням записаны\n"
    result_message += "📊 Сводка бонусов сохранена в лист 'сводка_бонусов'\n\n"
    result_message += "💰 ИТОГОВЫЕ БОНУСЫ:\n"
    
    # Показываем только бонусы (без окладов)
    total_bonuses_only = 0
    for _, row in bonus_summary_df.iterrows():
        if row['Тип'] == 'ОБЩАЯ СУММА':
            continue
        elif row['Тип'] == 'ROP сотрудники':
            # Для ROP вычитаем оклад
            oklad = salary_oklad['employee ROP'].iloc[0] if len(salary_oklad) > 0 else 0
            bonus_only = row['Сумма'] - oklad
            result_message += f"👤 {row['Тип']}: {bonus_only:,.0f} тенге\n"
            total_bonuses_only += bonus_only
        elif row['Тип'] in ['developer', 'assistant', 'assistant 2', 'supplier manager']:
            # Для разработчиков и ассистентов бонусов нет
            continue
        else:
            # Для менеджеров вычитаем оклад
            oklad = salary_oklad[row['Тип']].iloc[0] if len(salary_oklad) > 0 and row['Тип'] in salary_oklad.columns else 0
            bonus_only = row['Сумма'] - oklad
            result_message += f"👤 {row['Тип']}: {bonus_only:,.0f} тенге\n"
            total_bonuses_only += bonus_only
    
    result_message += f"🎯 ОБЩАЯ СУММА БОНУСОВ: {total_bonuses_only:,.0f} тенге\n"

    return result_message

def get_salary_summary():
    """Получить полную сводку по зарплатам (оклады + бонусы)"""
    try:
        excel_path = os.path.join(os.path.dirname(__file__), "..", "Alseit.xlsx")
        
        # Читаем данные
        salary = pd.read_excel(excel_path, sheet_name='зарплата')
        sales = pd.read_excel(excel_path, sheet_name='продажи')
        
        # Получаем оклады из первой строки
        salary_oklad = salary.iloc[[0]].copy()
        
        # Находим колонки менеджеров из таблицы зарплаты
        exclude_cols = ['date', 'order', 'developer', 'employee ROP', 'assistant', 'assistant 2', 'supplier manager']
        manager_cols = [col for col in salary.columns if col not in exclude_cols]
        
        # Рассчитываем бонусы от продаж используя ту же логику, что и в update_salary()
        # Создаем временные колонки для расчетов
        sales['temp_manager_bonus'] = 0.0
        sales['temp_salary_rop'] = 0.0
        sales['temp_profit'] = 0.0
        
        # Рассчитываем бонусы для каждой продажи
        for idx, row in sales.iterrows():
            boiler_name = row.get('boiler_name', '')
            payment_method = row.get('payment_method', 'наличные')
            quantity = row.get('quantity', 1)
            delivery = row.get('delivery', '')
            accessories = row.get('accessories', 0)
            
            # Пропускаем строки без названия котла
            if pd.isna(boiler_name) or boiler_name == '':
                continue
                
            # Убираем пробелы в начале и конце
            boiler_name = str(boiler_name).strip()
                
            # Обрабатываем NaN в payment_method
            if pd.isna(payment_method):
                payment_method = 'наличные'
            else:
                payment_str = str(payment_method).strip().lower()
                if payment_str in ['нал', 'наличные', 'наличка', 'cash']:
                    payment_method = 'наличные'
                elif payment_str in ['банк', 'банковский', 'карта', 'bank', 'card']:
                    payment_method = 'банк'
                else:
                    payment_method = 'наличные'  # По умолчанию
                
            # Обрабатываем NaN в quantity
            if pd.isna(quantity):
                quantity = 1
                
            # Обрабатываем delivery - определяем сумму доставки
            delivery_amount = 0
            if not pd.isna(delivery) and delivery != '':
                delivery_str = str(delivery).strip().lower()
                if delivery_str == 'пэй':
                    delivery_amount = 55000  # delivery_pay
                elif delivery_str == 'магазин':
                    delivery_amount = 4700   # delivery_shop
                else:
                    # Пытаемся извлечь число из строки
                    try:
                        delivery_amount = float(delivery_str)
                    except:
                        delivery_amount = 0
            
            # Обрабатываем NaN в accessories
            if pd.isna(accessories):
                accessories = 0
            else:
                try:
                    accessories = float(accessories)
                except:
                    accessories = 0
            
            manager_bonus, rop_bonus, profit = calculate_boiler_bonus(
                boiler_name, payment_method, delivery_amount, accessories, quantity
            )
            
            sales.loc[idx, 'temp_manager_bonus'] = manager_bonus
            sales.loc[idx, 'temp_salary_rop'] = rop_bonus
            sales.loc[idx, 'temp_profit'] = profit
        
        # Создаем словарь для группировки бонусов по дате и заказу
        bonus_dict = {}
        
        for idx, row in sales.iterrows():
            # Пропускаем только строки без названия котла
            if pd.isna(row['boiler_name']) or row['boiler_name'] == '':
                continue
                
            date = row['date']
            order = row['order']
            key = (date, order)
            
            if key not in bonus_dict:
                bonus_dict[key] = {
                    'date': date,
                    'order': order,
                    'employee ROP': 0,
                    'managers': {}
                }
            
            # Добавляем ROP бонус
            bonus_dict[key]['employee ROP'] += row['temp_salary_rop']
            
            # Добавляем бонус менеджера - проверяем все колонки менеджеров
            manager_name = row['manager']
            if manager_name in manager_cols:
                if manager_name not in bonus_dict[key]['managers']:
                    bonus_dict[key]['managers'][manager_name] = 0
                bonus_dict[key]['managers'][manager_name] += row['temp_manager_bonus']
        
        # Создаем строки для зарплаты
        rows = []
        for key, data in bonus_dict.items():
            new_row = {col: 0 for col in salary.columns}
            new_row['date'] = data['date']
            new_row['order'] = data['order']
            new_row['employee ROP'] = data['employee ROP']
            
            # Добавляем бонусы менеджеров
            for manager, bonus in data['managers'].items():
                new_row[manager] = bonus
                
            rows.append(new_row)
        
        sales_salary = pd.DataFrame(rows)
        
        # Создаем сводку по зарплатам
        salary_summary = []
        
        # ROP сотрудники (оклад + бонусы)
        rop_oklad = salary_oklad['employee ROP'].iloc[0] if len(salary_oklad) > 0 and 'employee ROP' in salary_oklad.columns else 0
        total_rop_bonus = sales_salary['employee ROP'].sum() if 'employee ROP' in sales_salary.columns else 0
        total_rop_salary = rop_oklad + total_rop_bonus
        salary_summary.append({
            'Тип': 'ROP сотрудники',
            'Оклад': rop_oklad,
            'Бонусы': total_rop_bonus,
            'Итого': total_rop_salary
        })
        
        # Разработчики и ассистенты (только оклады)
        fixed_salary_cols = ['developer', 'assistant', 'assistant 2', 'supplier manager']
        for col in fixed_salary_cols:
            if col in salary_oklad.columns:
                oklad = salary_oklad[col].iloc[0] if len(salary_oklad) > 0 else 0
                if oklad > 0:
                    salary_summary.append({
                        'Тип': col,
                        'Оклад': oklad,
                        'Бонусы': 0,
                        'Итого': oklad
                    })
        
        # Менеджеры (оклад + бонусы)
        for col in manager_cols:
            if col in sales_salary.columns:
                oklad = salary_oklad[col].iloc[0] if len(salary_oklad) > 0 and col in salary_oklad.columns else 0
                bonus_from_sales = sales_salary[col].sum()
                total_salary = oklad + bonus_from_sales
                
                if total_salary > 0:
                    salary_summary.append({
                        'Тип': col,
                        'Оклад': oklad,
                        'Бонусы': bonus_from_sales,
                        'Итого': total_salary
                    })
        
        # Формируем сообщение
        result_message = "💰 ПОЛНАЯ СВОДКА ПО ЗАРПЛАТАМ:\n\n"
        
        total_oklad = 0
        total_bonus = 0
        total_all = 0
        
        for item in salary_summary:
            result_message += f"👤 {item['Тип']}:\n"
            result_message += f"   💼 Оклад: {item['Оклад']:,.0f} тенге\n"
            if item['Бонусы'] > 0:
                result_message += f"   🎯 Бонусы: {item['Бонусы']:,.0f} тенге\n"
            result_message += f"   💰 Итого: {item['Итого']:,.0f} тенге\n\n"
            
            total_oklad += item['Оклад']
            total_bonus += item['Бонусы']
            total_all += item['Итого']
        
        result_message += f"📊 ОБЩИЕ СУММЫ:\n"
        result_message += f"💼 Всего окладов: {total_oklad:,.0f} тенге\n"
        result_message += f"🎯 Всего бонусов: {total_bonus:,.0f} тенге\n"
        result_message += f"💰 ОБЩАЯ СУММА: {total_all:,.0f} тенге"
        
        return result_message
        
    except Exception as e:
        return f"❌ Ошибка получения сводки зарплат: {str(e)}"

if __name__ == "__main__":
    print(update_salary())
