import telebot
import feedparser
import time
import os
import threading
from groq import Groq

# 1. Apne Details Yahan Daalein
TOKEN = "8649780443:AAFAyMv8-kMsQ5OlEgtuVLnkUGXEfjGtoM0"
CHANNEL_ID = "@mprogojo"
GROQ_API_KEY = "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"

bot = telebot.TeleBot(TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# 2. Feeds + YouTube Ka Naya Section Add Kiya Hai
RSS_FEEDS = {
    "📱 Tech & Xiaomi": "https://xiaomitime.com/feed/",
    "🎌 Anime Updates": "https://www.cbr.com/feed/category/anime/",
    "🎮 Gaming & Esports": "https://charlieintel.com/feed/",
    "▶️ YouTube Latest": "https://www.youtube.com/feeds/videos.xml?channel_id=UCXU2cO6O0kE0bS5wN-s6Hww" # Example YouTube ID
}

KEYWORDS = ["poco c3", "poco m5", "hp 15s", "free fire max", "gojo", "jujutsu kaisen", "hyperos", "xiaomi", "redmi"]
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
            model="llama-3.1-8b-instant", # Naya aur permanent fast model
        )
        return chat_completion.choices[0].message.content.strip()
    except Exception as e:
        return "Bhai update mast hai, link khol kar poori details check kar lo!"

# ==========================================
# 💬 NAYA FEATURE: TELEGRAM CHAT COMMANDS
# ==========================================

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    msg = "☠️ **Domain Expansion: JJK Tech V4.5!** ☠️\n\nBhai, main JJK Tech ka smart AI bot hoon. Yeh commands try karo:\n\n🔹 /tech - Latest Tech News\n🔹 /anime - Gojo & Anime Updates\n🔹 /ffcodes - Daily FF Codes\n🔹 /ffleaks - FF MAX Leaks & OB Updates"
    bot.reply_to(message, msg)

@bot.message_handler(commands=['ffleaks'])
def send_ff_leaks(message):
    # Free Fire MAX ke latest leaks aur OB update ki search
    bot.reply_to(message, "🔥 **Free Fire MAX Leaks & Updates!** 🔥\n\nBhai, naye OB update, upcoming Evo gun skins aur new characters ki khufiya details track ho rahi hain! Jaise hi koi confirm leak aayegi, JJK Tech par sabse pehle dhamaka hoga! 💥")

@bot.message_handler(commands=['ffcodes'])
def send_ff(message):
    # Pehle bot bolega ki woh dhoondh raha hai
    bot.reply_to(message, "🔍 Ek second bhai, internet se aaj ke ekdum fresh Free Fire MAX codes nikal raha hoon... ⏳")

    try:
        # Google News ka direct search link specifically FF codes ke liye
        ff_url = "https://news.google.com/rss/search?q=Free+Fire+MAX+redeem+codes+today&hl=en-IN&gl=IN&ceid=IN:en"
        feed = feedparser.parse(ff_url)

        if feed.entries:
            msg = "🎮 **Aaj Ke Free Fire MAX Redeem Codes!** 🎮\n\nBhai, internet par aaj ke fresh codes in links par aa gaye hain. Jaldi loot lo isse pehle ki limit cross ho jaye:\n\n"

            # Top 3 latest websites nikal kar dega
            for i in range(3):
                entry = feed.entries[i]
                msg += f"🔹 <b>{entry.title}</b>\n🔗 <a href='{entry.link}'>Yahan Se Codes Copy Karo</a>\n\n"

            bot.send_message(message.chat.id, msg, parse_mode="HTML")
        else:
            bot.send_message(message.chat.id, "Bhai abhi tak internet par aaj ke naye codes nahi aaye hain. Shaam ko try karna!")

    except Exception as e:
        bot.send_message(message.chat.id, "Bhai internet thoda slow chal raha hai, 5 minute baad wapas /ffcodes likhna!")


@bot.message_handler(commands=['anime', 'gojo'])
def send_anime(message):
    bot.reply_to(message, "🎌 **Anime Mode On!**\n\nGojo Satoru ki tarah limit-less updates ke liye channel ko check karte raho. Jujutsu Kaisen ki latest news Groq AI automatically post karta rahega! 🤞🔵🔴🟣")

# ==========================================
# 🔄 BACKGROUND NEWS SCANNER
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

                if link not in sent_links:
                    print(f"[{category}] Nayi news mili: {title}")
                    ai_summary = get_ai_summary(title)

                    title_lower = title.lower()
                    is_urgent = any(word in title_lower for word in KEYWORDS)

                    if is_urgent:
                        msg = f"🚨 <b>INSTANT ALERT: {category}</b> 🚨\n\n🔹 <b>{title}</b>\n\n🤖 <i>AI Summary:</i>\n{ai_summary}\n\n🔗 <a href='{link}'>Link</a>"
                    else:
                        msg = f"📰 <b>LATEST UPDATE: {category}</b>\n\n🔹 <b>{title}</b>\n\n🤖 <i>AI Summary:</i>\n{ai_summary}\n\n🔗 <a href='{link}'>Link</a>"

                    bot.send_message(CHANNEL_ID, msg, parse_mode="HTML")
                    save_link(link)
                    time.sleep(3)
        except Exception as e:
            pass

# Yeh function bot ko commands sunne ke liye hamesha on rakhega
def bot_polling():
    bot.infinity_polling()

print("☠️ JJK Tech Bot V4.5 (God Mode Ultra) Start Ho Gaya Hai! ☠️")

# Threading ka magic - Chat aur News dono ek sath chalenge!
threading.Thread(target=bot_polling, daemon=True).start()

while True:
    check_and_send_news()
    time.sleep(300)
