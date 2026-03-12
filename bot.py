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
    "📱 Tech & Xiaomi": "https://xiaomitime.com/feed/",
    "🎌 Anime Updates": "https://www.cbr.com/feed/category/anime/",
    "🔥 FF MAX Leaks": "https://news.google.com/rss/search?q=Free+Fire+MAX+OB+update+leaks+today&hl=en-IN&gl=IN&ceid=IN:en",
    "🤖 Android Authority": "https://www.androidauthority.com/feed/"
}

KEYWORDS = ["poco", "free fire", "gojo", "jujutsu kaisen", "hyperos", "xiaomi", "redmi", "ob update"]
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
# 📸 FEATURE 3: ROBUST IMAGE EXTRACTOR
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

def get_ai_analysis(title):
    try:
        prompt = f"""Tum ek hardcore tech aur gaming anchor ho. Is news title ko analyze karo: '{title}'.

        RULE 1: Agar yeh news kisi naye smartphone (jaise Poco, Xiaomi, iQOO, iPhone, etc.) ke launch, processor, ya hardware leak ki hai, toh uske specs internet/apni knowledge se nikal kar is format mein 'Spec-Sheet' likhna:
        📱 Display: [Screen details]
        ⬛ Processor: [Chipset name & details]
        📸 Camera: [Megapixel details]
        🔋 Battery: [mAh details]
        ⚡ Charging: [Watt details]
        💰 Price: [Expected price ya blank chhod do]

        RULE 2: Agar news Anime, Free Fire MAX, ya kisi normal app update ki hai, toh sirf 2-line mast casual Hinglish summary likhna.

        Dono rules ke hisaab se, bas EXACTLY is format mein reply dena:
        🤖 AI Summary:
        [Yahan RULE 1 ya RULE 2 ke hisaab se detail likho]

        🚀 Hype Level: [1 to 10]/10
        🔍 DRS Report: [🟢 Genuine / 🔴 Clickbait]
        🏷️ Tags: [#tag1 #tag2 #tag3]"""
        
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return f"🤖 AI Summary: Bhai mast update hai, details check karo!\n🚀 Hype Level: 7/10\n🔍 DRS Report: 🟢 Genuine\n🏷️ Tags: #JJKTech #Update"


# ==========================================
# 🚁 FEATURE 4: 7 PM THALA DIGEST THREAD
# ==========================================
def thala_digest_scheduler():
    global today_news_digest
    while True:
        ist_now = datetime.now(timezone.utc) + timedelta(hours=5, minutes=30)
        if ist_now.hour == 19 and ist_now.minute == 0:
            if len(today_news_digest) > 0:
                digest_msg = "🚁 **7 PM THALA DIGEST** 🚁\n\nBhai log, din bhar ki top 3 sabse badi khabarein ek sath:\n\n"
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
                    ai_data = get_ai_analysis(title)
                    img_url = get_image_from_feed(latest_post)
                    
                    title_lower = title.lower()
                    is_urgent = any(word in title_lower for word in KEYWORDS)
                    
                    msg_text = f"📰 <b>{category}</b>\n\n🔹 <b>{title}</b>\n\n{ai_data}"
                    if is_urgent:
                        msg_text = f"🚨 <b>PRIORITY ALERT: {category}</b> 🚨\n\n🔹 <b>{title}</b>\n\n{ai_data}"
                    
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("🔗 Pura Article Padho", url=link))
                    markup.add(InlineKeyboardButton("📤 Doston Ko Bhejo", url=f"https://t.me/share/url?url={link}&text=Bhai ye news check kar!"))

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
# 🛡️ DUMMY SERVER FOR RENDER (ANTI-CLONE TRICK)
# ==========================================
class DummyHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/plain')
        self.end_headers()
        self.wfile.write(b"JJK Tech Bot is Alive & Running! Render Khush Hai.")

def keep_alive_server():
    port = int(os.environ.get("PORT", 8080)) # Render automatically assigns this
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()
# ==========================================
# 🧪 THE "TEST" COMMAND (MANUAL CHECK)
# ==========================================
@bot.message_handler(commands=['testnews'])
def handle_testnews(message):
    # Command ke baad wala text nikalna
    title = message.text.replace("/testnews", "").strip()
    
    if not title:
        bot.reply_to(message, "Bhai, command ke baad phone ka naam bhi likho! Jaise: /testnews Poco M5 5G Launch Details")
        return
        
    bot.reply_to(message, "⏳ Thala AI dimaag laga raha hai... 5 sec ruko!")
    
    try:
        # AI se Spec-Sheet mangwana
        ai_data = get_ai_analysis(title)
        
        # Test result wapas bhejna
        msg_text = f"🛠️ <b>TESTING MODE</b>\n\n🔹 <b>{title}</b>\n\n{ai_data}"
        bot.reply_to(message, msg_text, parse_mode="HTML")
    except Exception as e:
        bot.reply_to(message, f"Error aa gaya bhai: {e}")
        
def bot_polling():
    bot.infinity_polling()

print("🚁 JJK Tech Bot V7.1 (Anti-Clone Edition) Start Ho Gaya Hai! 🚁")

# Start background threads
threading.Thread(target=keep_alive_server, daemon=True).start()
threading.Thread(target=bot_polling, daemon=True).start()
threading.Thread(target=thala_digest_scheduler, daemon=True).start()

while True:
    check_and_send_news()
    time.sleep(300)
