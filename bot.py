import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import time
import os
import threading
from datetime import datetime, timedelta, timezone
import re
from http.server import BaseHTTPRequestHandler, HTTPServer

# ==========================================
# 1. APNI DETAILS YAHAN DALO (NO AI KEY NEEDED NOW!)
# ==========================================
TOKEN = "8649780443:AAE_u3HM3jz-DKLWj8zmaeo9rdMcruIN1hw"
CHANNEL_ID = "@mprogojo"

bot = telebot.TeleBot(TOKEN)

# ==========================================
# 2. FEEDS AUR SETTINGS
# ==========================================
RSS_FEEDS = {
    "📱 TECH ALERT": "https://xiaomitime.com/feed/",
    "🎌 OTAKU UPDATE": "https://www.cbr.com/feed/category/anime/",
    "🎮 GAMING ZONE": "https://news.google.com/rss/search?q=Free+Fire+MAX+OB+update+leaks+today&hl=en-IN&gl=IN&ceid=IN:en",
    "🤖 ANDROID NEWS": "https://www.androidauthority.com/feed/",
    "https://rss.app/feeds/EeMhHchJsgWa4O1T.xml"
    # Agar RSS.app wali X (Twitter) ki link ho, toh upar wali line ke end mein comma (,) lagakar yahan daal dena.
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
# 🛠️ NAYE FEATURES: CLEANER & HASHTAGS
# ==========================================
def clean_html(raw_html):
    # HTML tags ko hatane ka engine
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', str(raw_html))
    return cleantext.strip()

def generate_hashtags(title):
    # Title se automatic tags bananeka system
    words = re.findall(r'\b\w+\b', title.lower())
    ignore_words = ['the', 'a', 'in', 'of', 'and', 'to', 'for', 'with', 'on', 'at', 'is', 'this', 'that', 'from', 'it']
    tags = [f"#{w.capitalize()}" for w in words if w not in ignore_words and len(w) > 3]
    return " ".join(tags[:4]) # Top 4 hashtags lagayega

# ==========================================
# 🔄 MAIN NEWS SCANNER (V8.0)
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
                    # 1. Clean Description (Short Summary)
                    raw_desc = latest_post.description if 'description' in latest_post else ""
                    clean_desc = clean_html(raw_desc)
                    if len(clean_desc) > 200:
                        clean_desc = clean_desc[:197] + "..." # Zyada lamba ho toh cut kar dega
                    if not clean_desc:
                        clean_desc = "Tap the link below to read the full exclusive story! 🔥"
                    
                    # 2. Extract Details
                    img_url = get_image_from_feed(latest_post)
                    auto_tags = generate_hashtags(title)
                    read_time = max(1, len(clean_desc.split()) // 20) # Read time logic
                    
                    title_lower = title.lower()
                    is_urgent = any(word in title_lower for word in KEYWORDS)
                    
                    # 3. Message Formatting
                    msg_text = f"<b>{category}</b>\n\n"
                    if is_urgent:
                        msg_text = f"🚨 <b>PRIORITY ALERT: {category}</b> 🚨\n\n"
                        
                    msg_text += f"🔹 <b>{title}</b>\n\n"
                    msg_text += f"📝 <i>{clean_desc}</i>\n\n"
                    msg_text += f"⏱️ <b>Est. Read:</b> {read_time} Min\n"
                    msg_text += f"🏷️ {auto_tags}\n"
                    
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("🔗 Read Full Article", url=link))
                    markup.add(InlineKeyboardButton("📤 Share", url=f"https://t.me/share/url?url={link}&text=Check out this latest update! 🔥"))

                    try:
                        if img_url:
                            sent_msg = bot.send_photo(CHANNEL_ID, img_url, caption=msg_text, parse_mode="HTML", reply_markup=markup)
                        else:
                            sent_msg = bot.send_message(CHANNEL_ID, msg_text, parse_mode="HTML", reply_markup=markup)
                        
                        if is_urgent:
                            bot.pin_chat_message(CHANNEL_ID, sent_msg.message_id)
                            
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
        self.wfile.write(b"JJK Tech Bot V8.0 (Raw Speed) is Alive!")

def keep_alive_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(('0.0.0.0', port), DummyHandler)
    server.serve_forever()

def bot_polling():
    bot.infinity_polling()

print("⚡ JJK Tech Bot V8.0 (No AI, Pure Speed) Start Ho Gaya Hai! ⚡")

threading.Thread(target=keep_alive_server, daemon=True).start()
threading.Thread(target=bot_polling, daemon=True).start()

while True:
    check_and_send_news()
    time.sleep(300) 
    
