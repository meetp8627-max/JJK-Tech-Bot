import telebot
import feedparser
import time
import os
import threading
from groq import Groq

# 1. Apne Details Yahan Daalein
TOKEN = "8649780443:AAEBBBVjrnm6xpk8WdukZndiK1-L5dVr6Z0"
CHANNEL_ID = "@mprogojo"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# 2. Feeds - FF Leaks ko direct Channel News mein add kar diya!
RSS_FEEDS = {
    "📱 Tech & Xiaomi": "https://xiaomitime.com/feed/",
    "🎌 Anime Updates": "https://www.cbr.com/feed/category/anime/",
    "🔥 FF MAX Leaks": "https://news.google.com/rss/search?q=Free+Fire+MAX+OB+update+leaks+today&hl=en-IN&gl=IN&ceid=IN:en"
}

KEYWORDS = ["poco", "free fire", "gojo", "jujutsu kaisen", "hyperos", "xiaomi", "redmi", "ob update"]
HISTORY_FILE = "sent_news.txt"

def load_sent_links():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r") as file:
            return file.read().splitlines()
    return []

def save_link(link):
    with open(HISTORY_FILE, "a") as file:
        file.write(link + "\n")

def get_ai_summary(title):
    try:
        prompt = f"Write a 2-line exciting summary in Hinglish for this news title: '{title}'. Use casual WhatsApp chat language."
        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.1-8b-instant",
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return "Bhai mast update hai, link open karke puri details check karo!"

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = "☠️ **Domain Expansion: JJK Tech V6.0!** ☠️\n\nMain 24/7 cloud par zinda hoon! Ab saari Tech, Anime aur Free Fire Leaks direct channel par aayegi AI summary ke sath. Purani news allowed nahi hai!"
    bot.reply_to(message, msg)

# ==========================================
# 🔄 SMART NEWS SCANNER (WITH TIME FILTER)
# ==========================================

def check_and_send_news():
    sent_links = load_sent_links()
    for category, url in RSS_FEEDS.items():
        try:
            feed = feedparser.parse(url)
            if feed.entries:
                latest_post = feed.entries[0]
                link = latest_post.link
                title = latest_post.title
                
                # ⏳ TIME FILTER: Check karo ki news kitni purani hai
                if hasattr(latest_post, 'published_parsed') and latest_post.published_parsed:
                    post_time = time.mktime(latest_post.published_parsed)
                    current_time = time.time()
                    
                    # Agar news 24 ghante (86400 seconds) se purani hai, toh chhod do
                    if current_time - post_time > 86400:
                        continue 
                
                if link not in sent_links:
                    print(f"[{category}] Nayi news mili: {title}")
                    ai_summary = get_ai_summary(title)
                    
                    title_lower = title.lower()
                    is_urgent = any(word in title_lower for word in KEYWORDS)
                    
                    if is_urgent:
                        msg = f"🚨 <b>INSTANT ALERT: {category}</b> 🚨\n\n🔹 <b>{title}</b>\n\n🤖 <i>AI Summary:</i>\n{ai_summary}\n\n🔗 <a href='{link}'>Pura article padhein</a>"
                    else:
                        msg = f"📰 <b>LATEST UPDATE: {category}</b>\n\n🔹 <b>{title}</b>\n\n🤖 <i>AI Summary:</i>\n{ai_summary}\n\n🔗 <a href='{link}'>Pura article padhein</a>"
                        
                    bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
                    save_link(link)
                    time.sleep(3)
        except Exception as e:
            pass

def bot_polling():
    bot.infinity_polling()

print("☠️ JJK Tech Bot V6.0 Start Ho Gaya Hai! ☠️")

threading.Thread(target=bot_polling, daemon=True).start()

while True:
    check_and_send_news()
    time.sleep(300)
