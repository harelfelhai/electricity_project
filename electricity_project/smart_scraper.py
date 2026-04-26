import google.generativeai as genai
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
from bs4 import BeautifulSoup
import json

# הגדרת המפתח שלך
GOOGLE_API_KEY = "AIzaSyBoVK4aJVnAXkY0cnsC2C0v6mFsYJD6YS8" # המפתח שקיבלת
genai.configure(api_key=GOOGLE_API_KEY)

def get_site_text(url):
    """שואב את הטקסט הגולמי מהאתר עם 'זהות' של דפדפן רגיל"""
    try:
        # אנחנו מוסיפים כאן 'User-Agent' כדי שהאתר יחשוב שאנחנו דפדפן כרום רגיל
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=15, verify=False)
        response.encoding = 'utf-8'
        
        if response.status_code != 200:
            return f"Error: קיבלנו קוד שגיאה {response.status_code} מהאתר"

        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ניקוי תגיות מיותרות
        for tag in soup(["script", "style", "nav", "footer", "header"]):
            tag.decompose()
            
        text = soup.get_text(separator=' ', strip=True)
        
        if len(text) < 100:
            return "Error: האתר החזיר טקסט קצר מדי, כנראה חסימת בוטים."
            
        return text
    except Exception as e:
        return f"Error fetching site: {e}"

def analyze_plans_with_gemini(site_text):
    """שולח את הטקסט ל-Gemini ומבקש ניתוח מסלולים"""
    model = genai.GenerativeModel('gemini-1.5-flash')
    
    prompt = f"""
    ניתוח מסלולי חשמל מהטקסט הבא:
    ---
    {site_text[:5000]} 
    ---
    תחזיר אך ורק אובייקט JSON (בלי מילים נוספות) שמכיל את המסלולים שמצאת.
    המבנה צריך להיות רשימה של אובייקטים:
    [
      {{"plan_name": "שם המסלול", "discount_pct": 5, "start_hour": 0, "end_hour": 24, "days": "all"}},
      ...
    ]
    אם מדובר בהנחה קבועה, השעות יהיו 0 עד 24.
    """
    
    response = model.generate_content(prompt)
    
    # ניקוי הטקסט שחוזר (לפעמים ה-AI מוסיף סימני Markdown של קוד)
    json_text = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(json_text)

# בדיקה על כתובת אמיתית (למשל סלקום אנרג'י)
# --- בדיקה עם הדפסות אבחון ---
target_url = "https://www.cellcom.co.il/energy"
print(f"1. מתחיל סריקה של: {target_url}...")

raw_text = get_site_text(target_url)

if "Error" in raw_text:
    print(f"שגיאה בשליפת האתר: {raw_text}")
else:
    print(f"2. האתר נסרק בהצלחה. אורך הטקסט שחולץ: {len(raw_text)} תווים.")
    print(f"--- הצצה לטקסט (500 תווים ראשונים): ---\n{raw_text[:500]}\n---")
    
    print("3. שולח ל-Gemini לניתוח... (זה עשוי לקחת זמן)")
    try:
        plans = analyze_plans_with_gemini(raw_text)
        print("\n4. הצלחנו! המסלולים שנמצאו:")
        print(json.dumps(plans, indent=4, ensure_ascii=False))
    except Exception as e:
        print(f"שגיאה בתקשורת עם Gemini: {e}")