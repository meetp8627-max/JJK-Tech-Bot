import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import time
import os
import threading
from datetime import datetime, timedelta, timezone
from groq import Groq
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==========================================
# 1. APNI DETAILS YAHAN DALO
# ==========================================
TOKEN = "8649780443:AAE_u3HM3jz-DKLWj8zmaeo9rdMcruIN1hw"
CHANNEL_ID = "@mprogojo"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# ==========================================
# 2. FEEDS AUR SETTINGS
# ==========================================
RSS_FEEDS = {
    "📱 TECH ALERT": "https://xiaomitime.com/feed/",
    "🎌 OTAKU UPDATE": "https://www.cbr.com/feed/category/anime/",
    "🎮 GAMING ZONE": "https://news.google.com/rss/search?q=Free+Fire+MAX+OB+update+leaks+today&hl=en-IN&gl=IN&ceid=IN:en",
    "🤖 ANDROID NEWS": "https://www.androidauthority.com/feed/",
    "🐦 X LEAKS (VIP)": "https://rss.app/feeds/EeMhHchJsgWa4O1T.xml" # <-- Naya Addition!
}
    
KEYWORDS = ["poco", "free fire", "gojo", "jujutsu kaisen", "hyperos", "xiaomi", "redmi", "ob update", "iphone"]
HISTORY_FILE = "sent_news.txt"
today_news_digest = []

def load_sent_links():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            return file.read().splitlines()
    return []

def save_link(link):
    with open(HISTORY_FILE, "a") as file:
        file.write(link + "\n")

# ==========================================
# 📸 THE ROBUST IMAGE EXTRACTOR
# ==========================================
def get_image_from_feed(entry):
    try:
        if 'media_content' in entry and entry.media_content:
            return entry.media_content[0]['url']
        if 'enclosures' in entry and entry.enclosures:
            for enc in entry.enclosures:
                if 'type' in enc and enc['type'].startswith('image/'):
                    return enc['href']
    except Exception:
        pass 

    search_text = ""
    if 'description' in entry:
        search_text += entry.description
    if 'content' in entry:
        search_text += entry.content[0].value

    if search_text:
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif))["\']', search_text, re.IGNORECASE)
        if img_match:
            img_url = img_match.group(1)
            if img_url.startswith('http'):
                return img_url
    return None

# ==========================================
# 🧠 V7.5 DIMAAG (ZERO FAKE, 100% FACTS)
# ==========================================
def get_ai_analysis(title, content=""):
    try:
        prompt = f"""Tum 'JJK Tech' Telegram channel ke official AI Anchor ho. 
        Tumhe is news ko padhna hai:
        Title: '{title}'
        Info: '{content}'

        STRICT RULES:
        1. Koi bhi fake specs ya details apne mann se nahi banani. Jo sach hai aur di gayi info me hai, bas wahi batao.
        2. Summary 3-4 lines ki ekdum hype wali 'Desi Hinglish' me honi chahiye. (Gamer aur Anime fans ke style me, jaise 'OP', 'Bawaal', 'Bhai log').
        3. Faltu ki overacting nahi karni.

        EXACTLY is format me reply do:
        🔥 **Highlight:**
        [Yahan apni mast 100% factual summary likho]

        🚀 **Hype Meter:** [1 to 10]/10
        🏷️ **Tags:** [#JJKTech #tag1 #tag2]"""
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
            temperature=0.2 # Extremely low temperature so it strictly sticks to facts
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return "🔥 **Highlight:**\nBhai log, ek mast update aayi hai! Fatafat link par click karke poori details check kar lo.\n\n🚀 **Hype Meter:** 8/10\n🏷️ **Tags:** #JJKTech #Update"

# ==========================================
# 🚁 7 PM THALA DIGEST THREAD
# ==========================================
def thala_digest_scheduler():
    global today_news_digest
    while True:
        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        if ist_now.hour == 19 and ist_now.minute == 0:
            if len(today_news_digest) > 0:
                digest_msg = "🚁 **7 PM THALA DIGEST** 🚁\n\nBhai log, din bhar ki top 3 OP khabarein ek sath:\n\n"
                for i, news in enumerate(today_news_digest[:3]):
                    digest_msg += f"🔥 {i+1}. <b>{news['title']}</b>\n🔗 <a href='{news['link']}'>Padho</a>\n\n"
                bot.send_message(CHANNEL_ID, digest_msg, parse_mode="HTML")
                today_news_digest.clear() 
            time.sleep(60) 
        time.sleep(30)

# ==========================================
# 🔄 MAIN NEWS SCANNER
# ==========================================
def check_and_send_news():
    global today_news_digest
    sent_links = load_sent_links()
    
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                latest_post = feed.entries[0]
                link = latest_post.link
                title = latest_post.title
                
                if hasattr(latest_post, 'published_parsed') and latest_post.published_parsed:
                    post_time = time.mktime(latest_post.published_parsed)
                    current_time = time.time()
                    if current_time - post_time > 86400:
                        continue 
                
                if link not in sent_links:
                    news_details = latest_post.description if 'description' in latest_post else ""
                    ai_data = get_ai_analysis(title, news_details)
                    img_url = get_image_from_feed(latest_post)
                    
                    title_lower = title.lower()
                    is_urgent = any(word in title_lower for word in KEYWORDS)
                    
                    msg_text = f"<b>{category}</b>\n\n🔹 <b>{title}</b>\n\n{ai_data}"
                    if is_urgent:
                        msg_text = f"🚨 <b>PRIORITY ALERT: {category}</b> 🚨\n\n🔹 <b>{title}</b>\n\n{ai_data}"
                    
                    # 🎮 THE SQUAD BUTTONS
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("🔗 Pura Article Padho", url=link))
                    markup.add(InlineKeyboardButton("📤 Squad Ko Bhejo", url=f"https://t.me/share/url?url={link}&text=Bhai JJK Tech ki ye news check kar! 🔥"))

                    try:
                        if img_url:
                            sent_msg = bot.send_photo(CHANNEL_ID, img_url, caption=msg_text, parse_mode="HTML", reply_markup=markup)
                        else:
                            sent_msg = bot.send_message(CHANNEL_ID, msg_text, parse_mode="HTML", reply_markup=markup)
                        
                        if is_urgent:
                            bot.pin_chat_message(CHANNEL_ID, sent_msg.message_id)
                            
                        today_news_digest.append({"title": title, "link": link})
                        save_link(link)
                        time.sleep(3)
                    except Exception as e:
                        print(f"Send Error: {e}")
        except Exception as e:
            pass

# ==========================================
# 🛡️ DUMMY SERVER FOR RENDER
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"JJK Tech Bot V7.5 is OP & Running!")

def keep_alive_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()
# ==========================================
# 🔍 THE SMART SPEC-CHECKER (ZERO FAKE ENGINE)
# ==========================================
@bot.message_handler(commands=['specs'])
def handle_specs(message):
    device_name = message.text.replace("/specs", "").strip()
    
    if not device_name:
        bot.reply_to(message, "Bhai, command ke baad phone ka naam bhi likho! Jaise: /specs Poco M5")
        return
        
    # GSMArena ka direct search link banayenge
    search_query = device_name.replace(" ", "+")
    gsm_link = f"https://www.gsmarena.com/results.php3?sName={search_query}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton(f"📱 Check {device_name.upper()} Specs", url=gsm_link))
    
    reply_text = f"🤖 Bhai, AI kabhi-kabhi specs mein hawa mein teer (hallucinate) maar deta hai.\n\nEkdum 100% asli aur official specs dekhne ke liye seedha is VIP button par click karo! 👇"
    
    bot.reply_to(message, reply_text, reply_markup=markup)
        
def bot_polling():
    bot.infinity_polling()

print("🤞 Domain Expansion: JJK Tech Bot V7.5 Start Ho Gaya Hai! 🔥")

threading.Thread(target=keep_alive_server, daemon=True).start()
threading.Thread(target=bot_polling, daemon=True).start()
threading.Thread(target=thala_digest_scheduler, daemon=True).start()

while True:
    check_and_send_news()
    time.sleep(300)
