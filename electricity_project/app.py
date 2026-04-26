import streamlit as st
import pandas as pd

# הגדרות דף
st.set_page_config(page_title="חשמל-לינק | חוסכים חכם", layout="wide", page_icon="💰")

# עיצוב RTL ושיפור נראות הטופס
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Assistant:wght@400;700&display=swap');
    html, body, .main { direction: rtl; text-align: right; font-family: 'Assistant', sans-serif; }
    .stButton>button { width: 100%; border-radius: 20px; background-color: #FFD700; color: black; font-weight: bold; border: none; }
    .lead-form { background-color: #f0f2f6; padding: 20px; border-radius: 15px; border-right: 5px solid #FFD700; }
    </style>
    """, unsafe_allow_html=True)

# כותרת שיווקית ובולטת
st.title("⚡ חוסכים במעבר בין ספקי חשמל")
st.subheader("גררו את הקובץ וגלו מיד כמה כסף מחכה לכם")

# פונקציות חישוב (נשארות אותו דבר)
PLANS = [
    {"company": "בזק אנרג'י", "plan_name": "הנחה קבועה (7%)", "discount_pct": 7, "type": "fixed", "start_hour": 0, "end_hour": 24},
    {"company": "פזגז חשמל", "plan_name": "הנחה קבועה (7%)", "discount_pct": 7, "type": "fixed", "start_hour": 0, "end_hour": 24},
    {"company": "סלקום אנרג'י", "plan_name": "עובדים מהבית (15%)", "discount_pct": 15, "type": "range", "start_hour": 8, "end_hour": 17},
]

def calculate_plan_cost(df, plan, base_price=0.60):
    discount = plan['discount_pct'] / 100
    if plan['type'] == 'fixed':
        return (df['צריכה/ייצור בקוט"ש'] * base_price * (1 - discount)).sum()
    else:
        start, end = plan['start_hour'], plan['end_hour']
        def apply_rate(row):
            in_range = start <= row['hour'] < end if start < end else row['hour'] >= start or row['hour'] < end
            return row['צריכה/ייצור בקוט"ש'] * (base_price * (1 - discount)) if in_range else row['צריכה/ייצור בקוט"ש'] * base_price
        return df.apply(apply_rate, axis=1).sum()

# --- המחשבון בפרונט ---
uploaded_file = st.file_uploader("מעלים כאן את קובץ ה-CSV מחברת החשמל", type="csv")

if uploaded_file:
    try:
        # 1. טעינה ראשונית של הקובץ
        df = pd.read_csv(uploaded_file, skiprows=10)
        df.columns = [col.strip() for col in df.columns]
        st.write(df.head())
        # 2. המרת סוגי נתונים (קריטי לסינון תאריכים)
        # ניסיון המרה גמיש יותר - מטפל בפורמט התאריך והשעה של חברת החשמל
        df['date_dt'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        
        # אם יש שורות שלא הומרו, ננסה לנקות תווים מיותרים ולנסות שוב
        if df['date_dt'].isna().any():
             df[date_col] = df[date_col].astype(str).str.replace(r'[^\d/ :]', '', regex=True)
             df['date_dt'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df['צריכה/ייצור בקוט"ש'] = pd.to_numeric(df['צריכה/ייצור בקוט"ש'], errors='coerce')
        df = df.dropna(subset=['צריכה/ייצור בקוט"ש'])
        df['hour'] = df['date_dt'].dt.hour
        
        # 3. כאן נכנס קוד בחירת טווח הזמנים (החדש):
        st.subheader("הגדרות ניתוח")
        analysis_mode = st.radio(
            "בחר את טווח הניתוח:",
            ["ניתוח כלל המידע שהועלה", "ניתוח טווח תאריכים ספציפי"],
            horizontal=True
        )

        # יצירת משתנה שיכיל את הנתונים לעיבוד (ברירת מחדל: הכל)
        df_filtered = df 

        if analysis_mode == "ניתוח טווח תאריכים ספציפי":
            min_date = df['date_dt'].min().date()
            max_date = df['date_dt'].max().date()
            
            col1, col2 = st.columns(2)
            with col1:
                start_date = st.date_input("תאריך התחלה", min_date, min_value=min_date, max_value=max_date)
            with col2:
                end_date = st.date_input("תאריך סיום", max_date, min_value=min_date, max_value=max_date)
            
            # ביצוע הסינון בפועל
            mask = (df['date_dt'].dt.date >= start_date) & (df['date_dt'].dt.date <= end_date)
            df_filtered = df.loc[mask]
            
            if df_filtered.empty:
                st.warning("לא נמצאו נתונים בטווח התאריכים הנבחר. מציג את כל המידע.")
                df_filtered = df

        # 4. ביצוע החישובים על בסיס הנתונים המסוננים (df_filtered)
        total_usage = df_filtered['צריכה/ייצור בקוט"ש'].sum()
        current_cost = total_usage * 0.60
        
        # חישוב כל מסלול מול הנתונים המסוננים
        results = []
        for plan in PLANS:
            new_cost = calculate_plan_cost(df_filtered, plan) # שימוש ב-df_filtered!
            results.append({
                "חברה": plan['company'], 
                "מסלול": plan['plan_name'], 
                "חיסכון": current_cost - new_cost
            })
        # הצגת התוצאה כ-Card בולט
        res_df = pd.DataFrame(results).sort_values(by="חיסכון", ascending=False)
        best_plan = res_df.iloc[0]
        st.success(f"### בטווח שנבחר, מצאנו לך חיסכון של ₪{res_df.iloc[0]['חיסכון']:.2f}!")
        st.write(f"המסלול המומלץ: **{best_plan['חברה']} - {best_plan['מסלול']}**")

        st.divider()

        # --- מנגנון הלידים (Call to Action) ---
        col_text, col_form = st.columns([1.5, 1])
        
        with col_text:
            st.write("### רוצה להתחיל לחסוך?")
            st.write("אין צורך להתקשר לחברות ולהמתין בתור. השאר פרטים ונציג מהחברה המשתלמת ביותר עבורך יחזור אליך להשלמת המעבר (ללא עלות).")
            st.info("💡 המעבר מתבצע מרחוק וללא צורך בטכנאי")

        with col_form:
            with st.container():
                st.markdown('<div class="lead-form">', unsafe_allow_html=True)
                with st.form("lead_form"):
                    name = st.text_input("שם מלא")
                    phone = st.text_input("מספר טלפון")
                    submitted = st.form_submit_button("אני רוצה לחסוך בחשמל")
                    
                    if submitted:
                        if name and phone:
                            # כאן בעתיד נשלח את הנתונים ל-Database
                            st.balloons()
                            st.success(f"תודה {name}, פרטיך הועברו לנציג {best_plan['חברה']}!")
                        else:
                            st.error("נא למלא שם וטלפון")
                st.markdown('</div>', unsafe_allow_html=True)

    except Exception as e:
        st.error("שגיאה בקריאת הקובץ. וודא שהעלית את הקובץ המקורי.")
