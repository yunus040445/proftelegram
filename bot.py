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
TOKEN = "8534122580:AAGRW6bWUnyHIYH7Xk1CvezfFOedmXp826g"
bot = Bot(token=TOKEN)

emoji_sets = ["💸💯👑", "✨💵🎉", "💎🤑🔥", "💰💎💯"]

# { user_id: {"name": str, "total": int} }
daily_approvals = {}
BLACKLIST = ["yat yok", "red", "onay yok", "yok"]

# ---------------------
# Flask keep-alive
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
# Admin kontrolü
# ---------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    return member.status in ["administrator", "creator"]

# ---------------------
# Mesaj dinleyici: onay/iptal/rapor
# ---------------------
async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message:
        return

    text = message.text.lower()

    # Admin kontrolü
    if not await is_admin(update, context):
        return

    # /rapor komutu
    if text.startswith("/rapor"):
        parts = text.split()
        if len(parts) < 2:
            await message.reply_text("Rapor almak için: /rapor KullaniciAdi")
            return
        target_name = parts[1]
        for data in daily_approvals.values():
            if data["name"].lower() == target_name.lower():
                toplam = data["total"]
                await message.reply_text(f"📊 {target_name} – Bugün\nToplam Onay: {toplam:,}")
                return
        await message.reply_text(f"{target_name} için kayıt bulunamadı.")
        return

    # Kara liste
    for word in BLACKLIST:
        if word in text and "iptal" not in text:
            return

    # Onay/iptal işlemi
    match = re.search(r'(\d+)\s?k?', text)
    if not match:
        return

    amount = int(match.group(1))
    if "k" in text:
        amount *= 1000
    if amount <= 0:
        return

    # Kullanıcı adını mesajdan alıyoruz (ör: Caner24 10k)
    user_match = re.match(r'(\w+)', text)
    if not user_match:
        return
    name = user_match.group(1)
    uid = hash(name.lower())  # basit ID, gerçek Telegram ID değil ama toplama için yeterli

    if uid not in daily_approvals:
        daily_approvals[uid] = {"name": name, "total": 0}

    # İptal
    if "iptal" in text:
        daily_approvals[uid]["total"] -= amount
        if daily_approvals[uid]["total"] < 0:
            daily_approvals[uid]["total"] = 0
        await message.reply_text(f"↩️ {name} için {amount:,} geri alındı\n📊 Güncel toplam: {daily_approvals[uid]['total']:,}")
        return

    # Normal onay
    daily_approvals[uid]["total"] += amount
    await message.reply_text(f"✅ {name} için {amount:,} onay kaydedildi\n📊 Bugünkü toplam: {daily_approvals[uid]['total']:,}")

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

        print("[GÜN SONU] Mesaj gönderildi:\n", mesaj)

# ---------------------
# Başlatma
# ---------------------
if __name__ == "__main__":
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("start", start))
    app_bot.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, approval_handler))

    # Gün sonu görevini başlat
    asyncio.get_event_loop().create_task(daily_message())

    # Polling başlat
    app_bot.run_polling()
