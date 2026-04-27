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
        
        # 2. המרת נתונים וניקוי שורות ריקות/שגויות
        
        # הגדרת שמות העמודות כפי שהן מופיעות בקובץ המקורי
        date_col = 'תאריך'
        time_col = 'מועד תחילת הפעימה'
        usage_col = 'צריכה/ייצור בקוט"ש'

        # וידוא שהעמודות קיימות ב-DataFrame
        if date_col in df.columns and time_col in df.columns:
            
            # א. ניקוי העמודות - הסרת רווחים לבנים ותווים נסתרים
            df[date_col] = df[date_col].astype(str).str.strip()
            df[time_col] = df[time_col].astype(str).str.strip()
            
            # ב. חיבור התאריך והשעה למחרוזת אחת
            # פורמט מצופה: "08/07/2025 00:00"
            df['combined_dt'] = df[date_col] + ' ' + df[time_col]
            
            # ג. המרה לאובייקט זמן (datetime)
            # dayfirst=True קריטי כדי ש-01/05 יתפרש כ-1 במאי ולא כ-5 בינואר
            df['date_dt'] = pd.to_datetime(df['combined_dt'], dayfirst=True, errors='coerce')
            
            # ד. טיפול בעמודת הצריכה (ניקוי גרשיים ופסיקים)
            df['usage'] = pd.to_numeric(
                df[usage_col].astype(str).str.replace('"', '').str.replace(',', '').str.strip(), 
                errors='coerce'
            )
            
            # ה. הסרת שורות שלא הצלחנו להמיר (שורות ריקות או כותרות משנה)
            df = df.dropna(subset=['date_dt', 'usage'])
            
            # ו. חילוץ שדות עזר לצורך סינון וחישוב
            df['hour'] = df['date_dt'].dt.hour
            df['only_date'] = df['date_dt'].dt.date
            df['day_of_week'] = df['date_dt'].dt.dayofweek # 0=יום שני, 6=יום ראשון (לפי פייתון)
            
            # נתקן את ימי השבוע שיתאימו לישראל (0=ראשון, 6=שבת)
            # פייתון נותן בברירת מחדל 0 ליום שני. נזיז את זה:
            df['israeli_day'] = (df['date_dt'].dt.dayofweek + 1) % 7
            
            st.success(f"הצלחנו לזהות {len(df)} שורות של נתונים.")
            st.info(f"טווח התאריכים בקובץ: {df['only_date'].min()} עד {df['only_date'].max()}")
        else:
            st.error(f"לא נמצאו העמודות הדרושות. העמודות שנמצאו: {', '.join(df.columns)}")
                
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
