import requests
from bs4 import BeautifulSoup
import json

def scrape_electricity_offer(url):
    try:
        # 1. שליפת תוכן האתר
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers)
        response.encoding = 'utf-8'
        
        # 2. ניקוי ה-HTML כדי להשאיר רק טקסט רלוונטי (חוסך "רעש" ל-AI)
        soup = BeautifulSoup(response.text, 'html.parser')
        for script in soup(["script", "style"]):
            script.extract()
        
        text = soup.get_text(separator='\n')
        # ניקוי רווחים מיותרים
        lines = [line.strip() for line in text.splitlines() if line.strip()]
        clean_text = "\n".join(lines[:100]) # לוקחים את ההתחלה שם בדרך כלל המבצעים

        # 3. כאן נכנס ה-AI (הסבר על הלוגיקה)
        # במקום לכתוב קוד שמחפש "5%", אנחנו נשלח את clean_text ל-API
        # ונבקש ממנו להחזיר JSON במבנה הבא:
        # {"company": "Bezeq", "discount": 0.07, "type": "fixed"}
        
        print(f"טקסט שחולץ מהאתר (דוגמה):\n{clean_text[:300]}...")
        return clean_text

    except Exception as e:
        return f"Error: {e}"

# נסה להריץ על כתובת אמיתית של אחת החברות
# scrape_electricity_offer("https://www.cellcom.co.il/energy")