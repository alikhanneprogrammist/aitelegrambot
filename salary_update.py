# salary_update.py
import pandas as pd
import numpy as np
import os
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
excel_file = os.getenv("EXCEL_FILE_NAME", "Alseit.xlsx")
excel_path = os.path.join(BASE_DIR, excel_file)

def update_salary():
    sales = pd.read_excel(excel_path, sheet_name="продажи")
    salary = pd.read_excel(excel_path, sheet_name="зарплата")

    # === 2. Расчеты ===
    vat_rate = float(os.getenv("VAT_RATE", "0.16"))
    low_price_threshold = float(os.getenv("LOW_PRICE_THRESHOLD", "300000"))
    low_price_deduction = float(os.getenv("LOW_PRICE_DEDUCTION", "50000"))
    high_price_deduction = float(os.getenv("HIGH_PRICE_DEDUCTION", "100000"))
    manager_bonus_rate = float(os.getenv("MANAGER_BONUS_RATE", "0.05"))
    rop_bonus_rate = float(os.getenv("ROP_BONUS_RATE", "0.01"))
    
    delivery_pay = float(os.getenv("DELIVERY_PAY", "55000"))
    delivery_shop = float(os.getenv("DELIVERY_SHOP", "4700"))
    
    # ИСПРАВЛЕНИЕ: Учитываем количество во всех расчетах
    sales['total_price'] = sales['price'] * sales['quantity']  # Общая стоимость
    sales['total_purchase'] = sales['purchase'] * sales['quantity']  # Общая закупка
    
    sales['vat'] = (sales['total_price'] * vat_rate).round(2)
    delivery_costs = {'пэй': delivery_pay, 'магазин': delivery_shop}
    sales['delivery_cost'] = sales['delivery'].map(delivery_costs).fillna(0)

    base_amount = sales['total_price'] - sales['vat'] - sales['delivery_cost']
    is_low_price = sales['total_price'] < low_price_threshold
    deduction = np.where(is_low_price, low_price_deduction, high_price_deduction)

    sales['manager_bonus'] = (base_amount - deduction) * manager_bonus_rate
    sales['salary_rop'] = (base_amount - deduction) * rop_bonus_rate
    sales['profit'] = (sales['total_price'] - sales['vat'] - sales['total_purchase'] -
                       sales['delivery_cost'] - sales['manager_bonus'] - sales['salary_rop'])

    # === 3. Готовим продажи для зарплаты ===
    sales['date'] = pd.to_datetime(sales['date'], errors='coerce')

    manager_cols = [c for c in salary.columns if c.startswith("manager_")]

    rows = []
    for _, row in sales.iterrows():
        new_row = {col: 0 for col in salary.columns}
        new_row['date'] = row['date']
        new_row['order'] = row['order']
        new_row['employee ROP'] = row['salary_rop']
        if row['manager'] in manager_cols:
            new_row[row['manager']] = row['manager_bonus']
        rows.append(new_row)

    sales_salary = pd.DataFrame(rows)

    # === 4. Склеиваем: оклад + продажи ===
    salary_oklad = salary.iloc[[0]].copy()
    salary_final = pd.concat([salary_oklad, sales_salary], ignore_index=True)

    # === 5. Создаем сводку по бонусам ===
    bonus_summary = []
    
    # Добавляем ROP бонусы
    total_rop_bonus = sales_salary['employee ROP'].sum()
    bonus_summary.append({
        'Тип': 'ROP сотрудники',
        'Сумма': total_rop_bonus
    })
    
    # Добавляем бонусы менеджеров
    for col in manager_cols:
        if col in sales_salary.columns:
            total_bonus = sales_salary[col].sum()
            if total_bonus > 0:
                bonus_summary.append({
                    'Тип': col,
                    'Сумма': total_bonus
                })
    
    # Добавляем общую сумму
    total_all_bonuses = total_rop_bonus + sum([item['Сумма'] for item in bonus_summary[1:]])
    bonus_summary.append({
        'Тип': 'ОБЩАЯ СУММА',
        'Сумма': total_all_bonuses
    })
    
    bonus_summary_df = pd.DataFrame(bonus_summary)

    # === 6. Сохраняем ===
    with pd.ExcelWriter(excel_path, mode="a", if_sheet_exists="replace", engine="openpyxl") as writer:
        salary_final.to_excel(writer, sheet_name="зарплата", index=False)
        bonus_summary_df.to_excel(writer, sheet_name="сводка_бонусов", index=False)

    # === 7. Формируем итоговое сообщение ===
    result_message = "✅ Salary обновлена: оклады + продажи по дням записаны\n"
    result_message += "📊 Сводка бонусов сохранена в лист 'сводка_бонусов'\n\n"
    result_message += "💰 ИТОГОВЫЕ БОНУСЫ:\n"
    
    for _, row in bonus_summary_df.iterrows():
        if row['Тип'] == 'ОБЩАЯ СУММА':
            result_message += f"🎯 {row['Тип']}: {row['Сумма']:,.2f} тенге\n"
        else:
            result_message += f"👤 {row['Тип']}: {row['Сумма']:,.2f} тенге\n"

    return result_message


if __name__ == "__main__":
    print(update_salary())
