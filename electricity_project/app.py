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
        # 1. טעינת הקובץ - בלי להציג כלום עדיין
        df = pd.read_csv(uploaded_file, skiprows=10)
        df.columns = [col.strip() for col in df.columns]
        
        target_col = 'צריכה/ייצור בקוט"ש'
        date_col = 'מועד תחילת הפעימה'
        
        # 2. המרת נתונים וניקוי שורות ריקות/שגויות
        df['date_dt'] = pd.to_datetime(df[date_col], dayfirst=True, errors='coerce')
        df['צריכה/ייצור בקוט"ש'] = pd.to_numeric(df[target_col], errors='coerce')
        
        # כאן אנחנו מוודאים שאנחנו עובדים רק עם שורות תקינות
        df = df.dropna(subset=['date_dt', 'צריכה/ייצור בקוט"ש'])
        df['hour'] = df['date_dt'].dt.hour
        
        if df.empty:
            st.error("לא נמצאו נתוני צריכה תקינים בקובץ. וודא שהעלית את הקובץ המקורי של חברת החשמל.")
        else:
            # 3. בחירת טווח
            st.subheader("📅 הגדרות ניתוח")
            analysis_mode = st.radio("בחר טווח:", ["כל התקופה", "טווח תאריכים ספציפי"], horizontal=True)
            
            # יצירת עמודת תאריך "נקייה" (בלי שעות) לצורך הסינון בלבד
            df['only_date'] = df['date_dt'].dt.date
            
            df_final = df.copy()
    
            if analysis_mode == "טווח תאריכים ספציפי":
                min_d = df['only_date'].min()
                max_d = df['only_date'].max()
                
                col1, col2 = st.columns(2)
                with col1:
                    start_selection = st.date_input("מתאריך", min_d)
                with col2:
                    end_selection = st.date_input("עד תאריך", max_d)
                
                # הסינון מתבצע עכשיו בין תאריך לתאריך (בלי שעות שיפריעו)
                mask = (df['only_date'] >= start_selection) & (df['only_date'] <= end_selection)
                df_final = df.loc[mask].copy()
                
                # בדיקה ויזואלית קריטית
                st.write(f"מספר שורות בטווח הנבחר: {len(df_final)}")            
            # 4. חישובים (חייבים לקרות על df_final)
            if df_final.empty:
                st.warning("⚠️ לא נמצאו נתונים בטווח התאריכים שנבחר. נסה לבחור טווח רחב יותר.")
            else:
                # עלות נוכחית בטווח הנבחר
                current_usage = df_final['צריכה/ייצור בקוט"ש'].sum()
                current_cost = current_usage * 0.60
                
                results = []
                for plan in PLANS:
                    # שים לב שאנחנו מעבירים את df_final לפונקציית החישוב
                    cost = calculate_plan_cost(df_final, plan)
                    results.append({
                        "חברה": plan['company'], 
                        "מסלול": plan['plan_name'], 
                        "חיסכון": current_cost - cost
                    })
                
                res_df = pd.DataFrame(results).sort_values(by="חיסכון", ascending=False)
                best_plan = res_df.iloc[0]
                
                # הצגת התוצאות
                st.success(f"### בטווח שנבחר, מצאנו לך חיסכון של ₪{best_plan['חיסכון']:.2f}!")

            # 5. רק עכשיו - הצגת התוצאות למשתמש!
            st.divider()
            st.success(f"### מצאנו לך חיסכון של ₪{best_plan['חיסכון']:.2f}!")
            st.info(f"המסלול המשתלם ביותר עבורך: **{best_plan['חברה']} - {best_plan['מסלול']}**")
            
            # הצגת הטבלה המלאה (אופציונלי)
            with st.expander("ראה פירוט של כל החברות"):
                st.dataframe(res_df, use_container_width=True, hide_index=True)

            # 6. טופס הלידים
            st.divider()
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.write("### רוצה להתחיל לחסוך?")
                st.write(f"השאר פרטים ונציג מ**{best_plan['חברה']}** יחזור אליך להמשך תהליך.")
            with c2:
                with st.form("lead_form"):
                    u_name = st.text_input("שם מלא")
                    u_phone = st.text_input("מספר טלפון")
                    if st.form_submit_button("אני רוצה לחסוך"):
                        if u_name and u_phone:
                            # פה נכניס בעתיד את השמירה ל-Google Sheets
                            st.balloons()
                            st.success("הפרטים נשמרו! נציג יחזור אליך בקרוב.")
                        else:
                            st.warning("נא למלא שם וטלפון")

    except Exception as e:
        # אם יש שגיאה, נציג אותה בצורה ברורה לדיבאג
        st.error(f"קרתה שגיאה בתהליך החישוב: {e}")
    except Exception as e:
        st.error("שגיאה בקריאת הקובץ. וודא שהעלית את הקובץ המקורי.")
