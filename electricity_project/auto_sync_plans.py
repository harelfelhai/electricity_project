import requests
from bs4 import BeautifulSoup
import google.generativeai as genai
import json
import os

# הגדרת המפתח
GOOGLE_API_KEY = "AIzaSyBoVK4aJVnAXkY0cnsC2C0v6mFsYJD6YS8"

def step_1_fetch_site():
    print("1. ניגש לאתר 'כמה זה'...")
    url = "https://www.kamaze.co.il/Compare/52/electrical-power"
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    try:
        # כאן אנחנו משתמשים ב-verify=False ישירות
        response = requests.get(url, headers=headers, verify=False, timeout=15)
        soup = BeautifulSoup(response.text, 'html.parser')
        text = soup.get_text(separator=' ', strip=True)
        
        with open("raw_site_data.txt", "w", encoding="utf-8") as f:
            f.write(text)
        print("✅ שלב 1 הסתיים: הטקסט מהאתר נשמר בקובץ raw_site_data.txt")
        return text
    except Exception as e:
        print(f"❌ שגיאה בשלב 1: {e}")
        return None

def step_2_analyze(raw_text):
    print("2. מנסה לשלוח ל-Gemini (דרך פרוטוקול REST פשוט)...")
    
    # הדרך הכי פחות "רגישה" לחסימות SSL בתוך הקוד
    os.environ['CURL_CA_BUNDLE'] = '' 
    genai.configure(api_key=GOOGLE_API_KEY, transport='rest')
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"Extract electricity plans from this text to a JSON list with: company, plan_name, discount_pct, type, start_hour, end_hour. Text: {raw_text[:5000]}"
    
    try:
        response = model.generate_content(prompt)
        print("✅ שלב 2 הסתיים: Gemini ענה!")
        return response.text
    except Exception as e:
        print(f"❌ שגיאה בשלב 2 (Gemini): {e}")
        return None

# הרצה
site_text = step_1_fetch_site()
if site_text:
    result = step_2_analyze(site_text)
    if result:
        print(result)