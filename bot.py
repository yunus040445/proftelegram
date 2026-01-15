import random
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
from flask import Flask
from threading import Thread
import asyncio

# Telegram Token ve Chat ID
TOKEN = "8534122580:AAF6bhd46cnOvT-sgX4iLfYEx_qa12BOEmU"
CHAT_ID = 5452763929

bot = Bot(token=TOKEN)

emoji_sets = [
    "💸💯👑",
    "✨💵🎉",
    "💎🤑🔥",
    "💰💎💯"
]

# ---------------------
# Flask server (keep-alive)
# ---------------------
app = Flask('')
@app.route('/')
def home():
    return "Bot aktif 🚀"
Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# /start komutu
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emojiler = random.choice(emoji_sets)
    mesaj = f"<b>{emojiler} —GÜN SONU— {emojiler}</b>"
    await context.bot.send_message(chat_id=update.effective_chat.id, text=mesaj, parse_mode='HTML')
    print("Test mesajı /start ile gönderildi")

# Gün sonu mesajı fonksiyonu
async def daily_message():
    while True:
        now = datetime.now()
        next_run = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)
        await asyncio.sleep((next_run - now).total_seconds())
        emojiler = random.choice(emoji_sets)
        mesaj = f"<b>{emojiler} —GÜN SONU— {emojiler}</b>"
        await bot.send_message(chat_id=CHAT_ID, text=mesaj, parse_mode='HTML')
        print(f"Gün sonu mesajı gönderildi: {mesaj}")

# ---------------------
# Botu başlat
# ---------------------
app_bot = ApplicationBuilder().token(TOKEN).build()
app_bot.add_handler(CommandHandler("start", start))

# background task için ayrı async fonksiyon
async def start_background_tasks():
    asyncio.create_task(daily_message())
    print("Background görevler başlatıldı")

# Railway'de zaten çalışan event loop var
loop = asyncio.get_event_loop()
loop.create_task(start_background_tasks())

# polling başlat
app_bot.run_polling()
