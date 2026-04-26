import pandas as pd
import os
import json

def load_electricity_data(file_path):
    if not os.path.exists(file_path):
        print(f"שגיאה: הקובץ {file_path} לא נמצא.")
        return None
    try:
        df = pd.read_csv(file_path, encoding='utf-8', skiprows=10)
        df.columns = [col.strip() for col in df.columns]
        relevant_columns = ['תאריך', 'מועד תחילת הפעימה', 'צריכה/ייצור בקוט"ש']
        df = df[relevant_columns]
        df['צריכה/ייצור בקוט"ש'] = pd.to_numeric(df['צריכה/ייצור בקוט"ש'], errors='coerce')
        df = df.dropna(subset=['צריכה/ייצור בקוט"ש'])
        # חילוץ שעה למטרת חישובים
        df['hour'] = df['מועד תחילת הפעימה'].str.split(':').str[0].astype(int)
        return df
    except Exception as e:
        print(f"קרתה שגיאה בקריאת הקובץ: {e}")
        return None

def calculate_plan_cost(df, plan, base_price_per_kwh=0.60):
    """מחשב עלות למסלול בודד מתוך ה-JSON"""
    discount = plan['discount_pct'] / 100
    
    if plan['type'] == 'fixed':
        # הנחה קבועה על כל הקוט"ש
        return (df['צריכה/ייצור בקוט"ש'] * base_price_per_kwh * (1 - discount)).sum()
    
    elif plan['type'] == 'range':
        # הנחה רק בשעות מסוימות
        start, end = plan['start_hour'], plan['end_hour']
        
        def apply_rate(row):
            # בדיקה אם השעה בטווח (מטפל גם בטווח שחוצה את חצות כמו 23 עד 7)
            if start < end:
                in_range = start <= row['hour'] < end
            else: # טווח לילה (למשל 23 עד 07)
                in_range = row['hour'] >= start or row['hour'] < end
                
            if in_range:
                return row['צריכה/ייצור בקוט"ש'] * (base_price_per_kwh * (1 - discount))
            return row['צריכה/ייצור בקוט"ש'] * base_price_per_kwh
            
        return df.apply(apply_rate, axis=1).sum()

# --- חלק ההרצה ---
csv_path = os.path.join('data', 'usage_data.csv')
# הנתיב לתיקייה שבה נמצא הסקריפט הנוכחי
script_dir = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(script_dir, 'plans.json')

df = load_electricity_data(csv_path)

if df is not None:
    if not os.path.exists(json_path):
        print("שגיאה: קובץ plans.json לא נמצא. הרץ קודם את ה-auto_sync.")
    else:
        with open(json_path, 'r', encoding='utf-8') as f:
            plans = json.load(f)
        
        base_price = 0.60
        total_usage = df['צריכה/ייצור בקוט"ש'].sum()
        current_cost = total_usage * base_price
        
        print("\n" + "="*60)
        print(f" {'דוח השוואת מסלולים דינמי':^58}")
        print("="*60)
        print(f"סה\"כ צריכה: {total_usage:.2f} קוט\"ש | עלות חברת חשמל: {current_cost:.2f} ש\"ח")
        print("-" * 60)
        print(f"{'חברה':<15} | {'מסלול':<20} | {'עלות חדשה':<10} | {'חיסכון':<8}")
        print("-" * 60)
        
        results = []
        for plan in plans:
            new_cost = calculate_plan_cost(df, plan, base_price)
            savings = current_cost - new_cost
            results.append({**plan, 'new_cost': new_cost, 'savings': savings})
        
        # מיון לפי החיסכון הגבוה ביותר
        for res in sorted(results, key=lambda x: x['savings'], reverse=True):
            print(f"{res['company']:<15} | {res['plan_name']:<20} | {res['new_cost']:>8.2f} ש\"ח | {res['savings']:>7.2f} ש\"ח")
            
        print("="*60)