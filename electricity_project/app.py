import streamlit as st
import pandas as pd
import json
import os

# 1. הגדרות דף ועיצוב RTL
st.set_page_config(page_title="מחשבון חיסכון בחשמל", layout="wide", page_icon="⚡")

# הזרקת CSS ליישור לימין ועיצוב כללי
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    
    html, body, [data-testid="stSidebar"], .main {
        direction: rtl;
        text-align: right;
        font-family: 'Assistant', sans-serif;
    }
    .stMetric {
        border: 1px solid #e6e9ef;
        padding: 15px;
        border-radius: 10px;
        background-color: #f8f9fb;
    }
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        color: #1f1f1f;
    }
    /* תיקון כיוון למספרים בתוך המטריקות */
    div[data-testid="stMetricValue"] > div {
        direction: ltr;
        display: inline-block;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("⚡ מחשבון חיסכון בחשמל")
st.subheader("גלה איזו חברה תחסוך לך הכי הרבה כסף בחשבון החשמל הבא")

# הוראות שימוש במרכז הדף
with st.expander("ℹ️ איך משתמשים במחשבון? (לחץ כאן)", expanded=False):
    st.write("""
    1. היכנסו לאתר חברת החשמל והורידו את קובץ נתוני הצריכה (CSV).
    2. העלו את הקובץ לכאן למטה.
    3. המערכת תנתח את הצריכה שלכם מול כל מסלולי החברות החדשות (בזק, סלקום, פזגז וכו').
    4. התוצאות יוצגו בטבלה ובגרף מפורטים.
    """)

# נתונים (אותם נתונים שהשתמשנו בהם קודם)
PLANS = [
    {"company": "בזק אנרג'י", "plan_name": "הנחה קבועה", "discount_pct": 7, "type": "fixed", "start_hour": 0, "end_hour": 24},
    {"company": "בזק אנרג'י", "plan_name": "חוסכים בלילה", "discount_pct": 20, "type": "range", "start_hour": 23, "end_hour": 7},
    {"company": "סלקום אנרג'י", "plan_name": "עובדים מהבית", "discount_pct": 15, "type": "range", "start_hour": 8, "end_hour": 17},
    {"company": "סלקום אנרג'י", "plan_name": "הנחה קבועה", "discount_pct": 5, "type": "fixed", "start_hour": 0, "end_hour": 24},
    {"company": "אלקטרה פאוור", "plan_name": "מסלול Power", "discount_pct": 5, "type": "fixed", "start_hour": 0, "end_hour": 24},
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
st.divider()
uploaded_file = st.file_uploader("גרור לכאן את קובץ ה-CSV שלך", type="csv")

if uploaded_file:
    try:
        df = pd.read_csv(uploaded_file, skiprows=10)
        df.columns = [col.strip() for col in df.columns]
        df['צריכה/ייצור בקוט"ש'] = pd.to_numeric(df['צריכה/ייצור בקוט"ש'], errors='coerce')
        df = df.dropna(subset=['צריכה/ייצור בקוט"ש'])
        df['hour'] = df['מועד תחילת הפעימה'].str.split(':').str[0].astype(int)
        
        total_usage = df['צריכה/ייצור בקוט"ש'].sum()
        current_cost = total_usage * 0.60
        
        # תצוגת מטריקות מעוצבת
        st.write("### תמונת מצב נוכחית")
        m1, m2, m3 = st.columns(3)
        m1.metric("סה\"כ צריכה", f"{total_usage:,.1f} קוט\"ש")
        m2.metric("עלות חברת חשמל (משוערת)", f"₪{current_cost:,.2f}")
        
        # חישוב
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
        
        # הצגת החיסכון המקסימלי במטריקה השלישית
        max_savings = res_df["חיסכון (₪)"].max()
        m3.metric("חיסכון מקסימלי אפשרי", f"₪{max_savings:,.2f}", delta=f"{max_savings/current_cost*100:.1f}%")

        st.divider()
        
        # גרף וטבלה בשני טורים
        c1, c2 = st.columns([1.2, 1])
        
        with c1:
            st.write("### השוואת חיסכון שקלי")
            # יצירת גרף עם צבע מותאם
            st.bar_chart(res_df.set_index("מסלול")["חיסכון (₪)"], color="#FFD700")
            
        with c2:
            st.write("### פירוט המסלולים")
            st.dataframe(res_df, use_container_width=True, hide_index=True)
            
        st.success(f"המסלול המשתלם ביותר עבורך הוא: **{res_df.iloc[0]['מסלול']}** של חברת **{res_df.iloc[0]['חברה']}**")

    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ. וודא שהעלית את הקובץ הנכון מחברת החשמל. ({e})")
