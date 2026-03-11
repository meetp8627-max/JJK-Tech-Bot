import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import feedparser
import time
import os
import threading
from datetime import datetime, timedelta
from groq import Groq
import re

# ==========================================
# 1. APNI DETAILS YAHAN DALO
# ==========================================
TOKEN = "8649780443:AAEBBBVjrnm6xpk8WdukZndiK1-L5dVr6Z0"
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
    "🔥 FF MAX Leaks": "https://news.google.com/rss/search?q=Free+Fire+MAX+OB+update+leaks+today&hl=en-IN&gl=IN&ceid=IN:en"
}

KEYWORDS = ["poco", "free fire", "gojo", "jujutsu kaisen", "hyperos", "xiaomi", "redmi", "ob update"]
HISTORY_FILE = "sent_news.txt"
today_news_digest = [] # Thala Digest ke liye memory

# Memory Load/Save
def load_sent_links():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            return file.read().splitlines()
    return []

def save_link(link):
    with open(HISTORY_FILE, "a") as file:
        file.write(link + "\n")

# ==========================================
# 📸 FEATURE 3: UPDATED IMAGE EXTRACTOR (ULTRA ROBUST)
# ==========================================
def get_image_from_feed(entry):
    # 1. Check Standard Media Tags (media:content) - Most Tech sites use this
    try:
        if 'media_content' in entry and entry.media_content:
            return entry.media_content[0]['url']
        # 2. Check Enclosures (Used by some feeds)
        if 'enclosures' in entry and entry.enclosures:
            for enc in entry.enclosures:
                if 'type' in enc and enc['type'].startswith('image/'):
                    return enc['href']
    except Exception:
        pass # Ignore if these tags don't exist

    # 3. Check inside HTML Content (Description or Full Content)
    # Combining description and full article content to find <img> tags.
    search_text = ""
    if 'description' in entry:
        search_text += entry.description
    if 'content' in entry:
        # content:encoded usually has full HTML
        search_text += entry.content[0].value

    if search_text:
        # Robust Regex: Finds <img src="..."> with single OR double quotes
        # Looks for valid image extensions: jpg, jpeg, png, webp, gif
        img_match = re.search(r'<img[^>]+src=["\']([^"\']+\.(?:jpg|jpeg|png|webp|gif))["\']', search_text, re.IGNORECASE)
        if img_match:
            img_url = img_match.group(1)
            # Ensure it's an absolute URL
            if img_url.startswith('http'):
                return img_url

    return None
# ==========================================
# 🚁 FEATURE 4: 7 PM THALA DIGEST THREAD
# ==========================================
def thala_digest_scheduler():
    global today_news_digest
    while True:
        # Render UTC mein chalta hai, toh IST (+5:30) mein convert kiya
        ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
        
        # Theek 7:00 PM baje
        if ist_now.hour == 19 and ist_now.minute == 0:
            if len(today_news_digest) > 0:
                digest_msg = "🚁 **7 PM THALA DIGEST** 🚁\n\nBhai log, din bhar ki top 3 sabse badi khabarein ek sath:\n\n"
                # Top 3 news nikalna
                for i, news in enumerate(today_news_digest[:3]):
                    digest_msg += f"🔥 {i+1}. <b>{news['title']}</b>\n🔗 <a href='{news['link']}'>Padho</a>\n\n"
                
                bot.send_message(CHANNEL_ID, digest_msg, parse_mode="HTML")
                today_news_digest.clear() # Agle din ke liye memory saaf
            time.sleep(60) # 1 minute wait taaki multiple message na jayein
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
                
                # 24 Hour Time Filter
                if hasattr(latest_post, 'published_parsed') and latest_post.published_parsed:
                    post_time = time.mktime(latest_post.published_parsed)
                    current_time = time.time()
                    if current_time - post_time > 86400:
                        continue 
                
                if link not in sent_links:
                    print(f"Nayi news: {title}")
                    ai_data = get_ai_analysis(title)
                    img_url = get_image_from_feed(latest_post)
                    
                    # Urgent Keyword Check for Auto-Pin
                    title_lower = title.lower()
                    is_urgent = any(word in title_lower for word in KEYWORDS)
                    
                    msg_text = f"📰 <b>{category}</b>\n\n🔹 <b>{title}</b>\n\n{ai_data}"
                    if is_urgent:
                        msg_text = f"🚨 <b>PRIORITY ALERT: {category}</b> 🚨\n\n🔹 <b>{title}</b>\n\n{ai_data}"
                    
                    # 🔘 FEATURE 1: VIP BUTTONS
                    markup = InlineKeyboardMarkup()
                    markup.add(InlineKeyboardButton("🔗 Pura Article Padho", url=link))
                    markup.add(InlineKeyboardButton("📤 Doston Ko Bhejo", url=f"https://t.me/share/url?url={link}&text=Bhai ye news check kar!"))

                    # Send Photo or Text
                    try:
                        if img_url:
                            # 📸 FEATURE 3: Auto Thumbnail
                            sent_msg = bot.send_photo(CHANNEL_ID, img_url, caption=msg_text, parse_mode="HTML", reply_markup=markup)
                        else:
                            sent_msg = bot.send_message(CHANNEL_ID, msg_text, parse_mode="HTML", reply_markup=markup)
                        
                        # 📌 FEATURE 2: Auto-Pin
                        if is_urgent:
                            bot.pin_chat_message(CHANNEL_ID, sent_msg.message_id)
                            
                        # Add to Digest
                        today_news_digest.append({"title": title, "link": link})
                        save_link(link)
                        time.sleep(3)
                        
                    except Exception as e:
                        print(f"Telegram bhejne mein error: {e}")
                        
        except Exception as e:
            pass

def bot_polling():
    bot.infinity_polling()

print("🚁 JJK Tech Bot V7.0 (Thala Edition) Start Ho Gaya Hai! 🚁")

# Start background threads
threading.Thread(target=bot_polling, daemon=True).start()
threading.Thread(target=thala_digest_scheduler, daemon=True).start()

while True:
    check_and_send_news()
    time.sleep(300)
