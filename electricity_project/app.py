import streamlit as st
import pandas as pd
import json
import os

# הגדרות דף
st.set_page_config(page_title="מחשבון חיסכון בחשמל", layout="wide")

st.title("⚡ מחשבון חיסכון בחשמל - מהפכת החשמל")
st.write("העלה את קובץ הצריכה שלך וגלה כמה תוכל לחסוך בכל חברה")

# נתונים (אותם נתונים מה-JSON)
PLANS = [
    {"company": "בזק אנרג'י", "plan_name": "הנחה קבועה", "discount_pct": 7, "type": "fixed", "start_hour": 0, "end_hour": 24},
    {"company": "בזק אנרג'י", "plan_name": "חוסכים בלילה", "discount_pct": 20, "type": "range", "start_hour": 23, "end_hour": 7},
    {"company": "סלקום אנרג'י", "plan_name": "עובדים מהבית", "discount_pct": 15, "type": "range", "start_hour": 8, "end_hour": 17},
    {"company": "סלקום אנרג'י", "plan_name": "הנחה קבועה", "discount_pct": 5, "type": "fixed", "start_hour": 0, "end_hour": 24},
    {"company": "פזגז חשמל", "plan_name": "הנחה קבועה", "discount_pct": 7, "type": "fixed", "start_hour": 0, "end_hour": 24}
]

def calculate_plan_cost(df, plan, base_price=0.60):
    discount = plan['discount_pct'] / 100
    if plan['type'] == 'fixed':
        return (df['צריכה/ייצור בקוט"ש'] * base_price * (1 - discount)).sum()
    else:
        start, end = plan['start_hour'], plan['end_hour']
        def apply_rate(row):
            if start < end: in_range = start <= row['hour'] < end
            else: in_range = row['hour'] >= start or row['hour'] < end
            return row['צריכה/ייצור בקוט"ש'] * (base_price * (1 - discount)) if in_range else row['צריכה/ייצור בקוט"ש'] * base_price
        return df.apply(apply_rate, axis=1).sum()

# העלאת קובץ
uploaded_file = st.file_uploader("בחר קובץ CSV שהורדת מחברת החשמל", type="csv")

if uploaded_file:
    try:
        # עיבוד הקובץ
        df = pd.read_csv(uploaded_file, skiprows=10)
        df.columns = [col.strip() for col in df.columns]
        df['צריכה/ייצור בקוט"ש'] = pd.to_numeric(df['צריכה/ייצור בקוט"ש'], errors='coerce')
        df = df.dropna(subset=['צריכה/ייצור בקוט"ש'])
        df['hour'] = df['מועד תחילת הפעימה'].str.split(':').str[0].astype(int)
        
        # חישוב בסיסי
        total_usage = df['צריכה/ייצור בקוט"ש'].sum()
        current_cost = total_usage * 0.60
        
        # הצגת נתונים בסיסיים
        col1, col2 = st.columns(2)
        col1.metric("סה\"כ צריכה", f"{total_usage:.2f} קוט\"ש")
        col2.metric("עלות נוכחית (משוערת)", f"₪{current_cost:.2f}")
        
        # חישוב כל המסלולים
        results = []
        for plan in PLANS:
            new_cost = calculate_plan_cost(df, plan)
            savings = current_cost - new_cost
            results.append({
                "חברה": plan['company'],
                "מסלול": plan['plan_name'],
                "עלות חדשה": round(new_cost, 2),
                "חיסכון (₪)": round(savings, 2)
            })
        
        res_df = pd.DataFrame(results).sort_values(by="חיסכון (₪)", ascending=False)
        
        # הצגת טבלה מעוצבת
        st.subheader("תוצאות ההשוואה")
        st.dataframe(res_df, use_container_width=True)
        
        # בונוס: גרף חיסכון
        st.bar_chart(res_df.set_index("מסלול")["חיסכון (₪)"])
        
    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ: {e}")