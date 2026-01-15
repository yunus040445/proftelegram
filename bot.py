import random
import re
from datetime import datetime, timedelta
from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)
from flask import Flask
from threading import Thread
import asyncio

# ---------------------
# Ayarlar
# ---------------------
TOKEN = "8534122580:AAF6bhd46cnOvT-sgX4iLfYEx_qa12BOEmU"
CHAT_ID = 5452763929  # Botun çalışacağı tek grup ID'si
bot = Bot(token=TOKEN)

emoji_sets = [
    "💸💯👑",
    "✨💵🎉",
    "💎🤑🔥",
    "💰💎💯"
]

# Günlük onay kayıtları: { user_id: {"name": str, "total": int} }
daily_approvals = {}

# Kara liste (bu kelimeleri içeren mesajlar işlenmez)
BLACKLIST = ["yat yok", "red", "onay yok", "yok"]

# ---------------------
# Flask keep-alive (Railway vs için)
# ---------------------
app = Flask('')
@app.route('/')
def home():
    return "Bot aktif 🚀"

Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ---------------------
# /start komutu
# ---------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    emojiler = random.choice(emoji_sets)
    mesaj = f"<b>{emojiler} —GÜN SONU— {emojiler}</b>"
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=mesaj,
        parse_mode='HTML'
    )

# ---------------------
# Admin kontrol fonksiyonu
# ---------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ["administrator", "creator"]

# ---------------------
# Onay ve iptal işlemleri için mesaj dinleyici
# ---------------------
async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.reply_to_message:
        return

    if message.chat.id != CHAT_ID:
        return

    text = message.text.lower()

    # Admin kontrolü
    if not await is_admin(update, context):
        return

    # Rapor komutu (reply olarak /rapor yazılınca)
    if text.strip() == "/rapor":
        target = message.reply_to_message.from_user
        data = daily_approvals.get(target.id)

        toplam = data["total"] if data else 0
        await message.reply_text(
            f"📊 {target.first_name} – Bugün\n"
            f"Toplam Onay: {toplam:,}"
        )
        return

    # Kara liste kontrolü (iptal kelimesi harici)
    for word in BLACKLIST:
        if word in text and "iptal" not in text:
            return

    # Sayı yakala
    match = re.search(r'(\d+)\s?k?', text)
    if not match:
        return

    amount = int(match.group(1))
    if "k" in match.group(0):
        amount *= 1000
    if amount <= 0:
        return

    target = message.reply_to_message.from_user
    uid = target.id
    name = target.first_name

    if uid not in daily_approvals:
        daily_approvals[uid] = {"name": name, "total": 0}

    # İptal işlemi
    if "iptal" in text:
        daily_approvals[uid]["total"] -= amount
        if daily_approvals[uid]["total"] < 0:
            daily_approvals[uid]["total"] = 0

        await message.reply_text(
            f"↩️ {name} için {amount:,} geri alındı\n"
            f"📊 Güncel toplam: {daily_approvals[uid]['total']:,}"
        )
        return

    # Normal onay işlemi
    daily_approvals[uid]["total"] += amount

    await message.reply_text(
        f"✅ {name} için {amount:,} onay kaydedildi\n"
        f"📊 Bugünkü toplam: {daily_approvals[uid]['total']:,}"
    )

# ---------------------
# Gün sonu mesajı ve özet (23:59)
# ---------------------
async def daily_message():
    global daily_approvals
    while True:
        now = datetime.now()
        next_run = now.replace(hour=23, minute=59, second=0, microsecond=0)
        if now >= next_run:
            next_run += timedelta(days=1)

        await asyncio.sleep((next_run - now).total_seconds())

        emojiler = random.choice(emoji_sets)
        mesaj = f"<b>{emojiler} —GÜN SONU— {emojiler}</b>"

        if daily_approvals:
            mesaj += "\n\n📊 <b>Günlük Özet</b>\n"
            for data in daily_approvals.values():
                mesaj += f"• {data['name']}: {data['total']:,}\n"

        await bot.send_messa_
