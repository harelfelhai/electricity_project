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
        # עיבוד מהיר
        df = pd.read_csv(uploaded_file, skiprows=10)
        df.columns = [col.strip() for col in df.columns]
        df['צריכה/ייצור בקוט"ש'] = pd.to_numeric(df['צריכה/ייצור בקוט"ש'], errors='coerce')
        df = df.dropna(subset=['צריכה/ייצור בקוט"ש'])
        df['hour'] = df['מועד תחילת הפעימה'].str.split(':').str[0].astype(int)
        
        current_cost = df['צריכה/ייצור בקוט"ש'].sum() * 0.60
        
        results = []
        for plan in PLANS:
            new_cost = calculate_plan_cost(df, plan)
            results.append({"חברה": plan['company'], "מסלול": plan['plan_name'], "חיסכון": current_cost - new_cost})
        
        res_df = pd.DataFrame(results).sort_values(by="חיסכון", ascending=False)
        best_plan = res_df.iloc[0]

        # הצגת התוצאה כ-Card בולט
        st.success(f"### מצאנו לך חיסכון של ₪{best_plan['חיסכון']:.2f}!")
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
