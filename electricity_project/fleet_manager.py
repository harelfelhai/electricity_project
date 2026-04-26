import requests
from bs4 import BeautifulSoup

# רשימת ה"מטרות" שלנו - בהמשך ה-AI יוכל להוסיף לכאן חברות חדשות שמצא בגוגל
COMPANIES_TO_SCRAPE = [
    {"name": "סלקום אנרג'י", "url": "https://www.cellcom.co.il/energy"},
    {"name": "בזק אנרג'י", "url": "https://www.bezeq.co.il/energy/"},
    {"name": "אמישראגז חשמל", "url": "https://www.amisragas.co.il/electricity/"}
]

def discover_new_companies():
    """
    כאן בעתיד נחבר API של גוגל שיחפש חברות חדשות
    ויחזיר שמות וכתובות אתרים שלא מופיעים ב-COMPANIES_TO_SCRAPE
    """
    print("מחפש חברות חדשות בשוק...")
    # לבינתיים נחזיר רשימה קבועה
    return COMPANIES_TO_SCRAPE

def get_site_content(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, 'html.parser')
        # שואבים רק את הטקסט המשמעותי
        return soup.get_text()
    except:
        return ""

def analyze_with_ai(text):
    """
    כאן נשלח את הטקסט ל-Gemini API
    נבקש ממנו: "חלץ את אחוזי ההנחה והשעות מתוך הטקסט הבא"
    """
    # זו סימולציה של מה שה-AI יחזיר לנו
    return {
        "fixed_discount": 0.05,
        "night_discount": 0.20,
        "is_active": True
    }

# הרצה לדוגמה
companies = discover_new_companies()
for comp in companies:
    print(f"סורק את {comp['name']}...")
    content = get_site_content(comp['url'])
    data = analyze_with_ai(content)
    print(f"נתונים שנמצאו: {data}")