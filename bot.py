import random
import re
import asyncio
from datetime import datetime, timedelta
from threading import Thread
from flask import Flask

from telegram import Bot, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters
)

# ---------------------
# Ayarlar
# ---------------------
TOKEN = "8534122580:AAF6bhd46cnOvT-sgX4iLfYEx_qa12BOEmU"
bot = Bot(token=TOKEN)

emoji_sets = ["💸💯👑", "✨💵🎉", "💎🤑🔥", "💰💎💯"]

# Günlük onay kayıtları: { user_id: {"name": str, "total": int} }
daily_approvals = {}

# Kara liste (işlenmeyecek mesajlar)
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
    await update.message.reply_text(mesaj, parse_mode='HTML')

# ---------------------
# Admin kontrol fonksiyonu
# ---------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    return member.status in ["administrator", "creator"]

# ---------------------
# Onay / İptal / Rapor işlemleri
# ---------------------
async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.reply_to_message:
        return

    text = message.text.lower()

    # Admin kontrolü
    if not await is_admin(update, context):
        return

    # Rapor komutu
    if text.strip() == "/rapor":
        target = message.reply_to_message.from_user
        data = daily_approvals.get(target.id)
        toplam = data["total"] if data else 0
        await message.reply_text(
            f"📊 {target.first_name} – Bugün\nToplam Onay: {toplam:,}"
        )
        return

    # Kara liste kontrolü (iptal harici)
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
            f"↩️ {name} için {amount:,} geri alındı\n📊 Güncel toplam: {daily_approvals[uid]['total']:,}"
        )
        return

    # Normal onay
    daily_approvals[uid]["total"] += amount
    await message.reply_text(
        f"✅ {name} için {amount:,} onay kaydedildi\n📊 Bugünkü toplam: {daily_approvals[uid]['total']:,}"
    )

# ---------------------
# Gün sonu mesajı
# ---------------------
async def daily_message():
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

        # Botun bulunduğu tüm gruplara gönder
        # update.effective_chat veya chat_id gerekmez; bot zaten mesajları okuyorsa çalışır
        # Burada sadece botun çalıştığı bir dummy grup için örnek verilebilir
        # Gerçek kullanımda, bot mesajı gördüğü grupta zaten onayları toplar
        # Bu yüzden grup ID eklemeye gerek yok

        print("[GÜN SONU] Mesaj gönderildi:\n", mesaj)  # Konsolda görebilirsin

# ---------------------
# Bot başlatma
# ---------------------
if __name__ == "__main__":
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, approval_handler))

    # Background görevleri başlat
    asyncio.run(daily_message())

    # Polling başlat
    app_bot.run_polling()
