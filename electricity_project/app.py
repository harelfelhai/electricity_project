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
        # --- שלב 1: זיהוי אוטומטי של תחילת הטבלה ---
        content = uploaded_file.getvalue().decode('utf-8').splitlines()
        header_row_index = 0
        for i, line in enumerate(content):
            if "תאריך" in line and "מועד תחילת הפעימה" in line:
                header_row_index = i
                break
        
        uploaded_file.seek(0)
        df = pd.read_csv(uploaded_file, skiprows=header_row_index)
        df.columns = [col.strip() for col in df.columns]
        
        # --- שלב 2: זיהוי עמודות והמרת נתונים ---
        date_col = 'תאריך'
        time_col = 'מועד תחילת הפעימה'
        usage_col = 'צריכה/ייצור בקוט"ש'
        
        if date_col in df.columns and time_col in df.columns:
            # חיבור תאריך ושעה
            df['full_dt_str'] = df[date_col].astype(str).str.strip() + ' ' + df[time_col].astype(str).str.strip()
            df['date_dt'] = pd.to_datetime(df['full_dt_str'], dayfirst=True, errors='coerce')
            
            # תיקון השגיאה: ניקוי תווים לא מספריים והמרה למספר
            df[usage_col] = df[usage_col].astype(str).str.replace('"', '').str.replace(',', '').str.strip()
            df['usage'] = pd.to_numeric(df[usage_col], errors='coerce')
            
            df = df.dropna(subset=['date_dt', 'usage'])
            
            if df.empty:
                st.error("לא נמצאו נתונים תקינים. וודא שהקובץ מכיל נתוני צריכה.")
            else:
                df['hour'] = df['date_dt'].dt.hour
                df['only_date'] = df['date_dt'].dt.date
                
                # --- שלב 3: הגדרות ניתוח ---
                st.subheader("📅 הגדרות ניתוח")
                actual_min = df['only_date'].min()
                actual_max = df['only_date'].max()
                
                analysis_mode = st.radio("בחר טווח:", ["כל התקופה", "טווח תאריכים ספציפי"], horizontal=True)
                
                df_final = df.copy()
                if analysis_mode == "טווח תאריכים ספציפי":
                    col1, col2 = st.columns(2)
                    with col1:
                        s_date = st.date_input("מתאריך", actual_min, min_value=actual_min, max_value=actual_max)
                    with col2:
                        e_date = st.date_input("עד תאריך", actual_max, min_value=actual_min, max_value=actual_max)
                    mask = (df['only_date'] >= s_date) & (df['only_date'] <= e_date)
                    df_final = df.loc[mask].copy()

                # --- שלב 4: חישובים ---
                if not df_final.empty:
                    # שימוש ב-float() כדי למנוע את שגיאת ה-String Multiply
                    total_kwh = float(df_final['usage'].sum())
                    current_cost = total_kwh * 0.60
                    
                    results = []
                    for plan in PLANS:
                        # שים לב שאנחנו שולחים לחישוב את df_final עם שם העמודה המקורי שהפונקציה מצפה לו
                        df_for_calc = df_final.rename(columns={'usage': 'צריכה/ייצור בקוט"ש'})
                        cost = calculate_plan_cost(df_for_calc, plan)
                        results.append({
                            "חברה": plan['company'], 
                            "מסלול": plan['plan_name'], 
                            "חיסכון": current_cost - float(cost)
                        })
                    
                    res_df = pd.DataFrame(results).sort_values(by="חיסכון", ascending=False)
                    best_plan = res_df.iloc[0]
                    
                    st.divider()
                    st.success(f"### מצאנו לך חיסכון של ₪{best_plan['חיסכון']:.2f}!")
                    st.info(f"המסלול המומלץ: **{best_plan['חברה']} - {best_plan['מסלול']}**")
                    
                    with st.expander("ראה פירוט של כל החברות"):
                        st.dataframe(res_df, use_container_width=True, hide_index=True)
        else:
            st.error("לא נמצאו עמודות 'תאריך' ו-'מועד תחילת הפעימה'.")

    except Exception as e:
        st.error(f"שגיאה בעיבוד הקובץ: {e}")
    except Exception as e:
        st.error("שגיאה בקריאת הקובץ. וודא שהעלית את הקובץ המקורי.")
