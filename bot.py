import re
import random
import asyncio
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

# ---------------------
# Ayarlar
# ---------------------
TOKEN = "BOT_TOKENIN"  # Buraya kendi tokenını koy
bot = Bot(token=TOKEN)

emoji_sets = ["💸💯👑", "✨💵🎉", "💎🤑🔥", "💰💎💯"]
daily_approvals = {}  # {user_id: {"name": str, "total": int}}
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
# Admin kontrol fonksiyonu
# ---------------------
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await context.bot.get_chat_member(
        update.effective_chat.id,
        update.effective_user.id
    )
    return member.status in ["administrator", "creator"]

# ---------------------
# /rapor komutu
# ---------------------
async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Bu komutu sadece admin kullanabilir.")
        return

    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Kullanıcı adı belirt: /rapor @kullanici")
        return

    username = args[0].lstrip("@")
    # Kullanıcıyı bul
    for data in daily_approvals.values():
        if data["username"].lower() == username.lower():
            await update.message.reply_text(
                f"📊 {data['name']} – Bugün\nToplam Onay: {data['total']:,}"
            )
            return

    await update.message.reply_text("⚠️ Bu kullanıcıya ait veri bulunamadı.")

# ---------------------
# Onay ve iptal mesajlarını yakala
# ---------------------
async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    # Admin kontrolü
    if not await is_admin(update, context):
        return

    text = message.text.lower()

    # Kara liste kontrolü
    if any(word in text and "iptal" not in text for word in BLACKLIST):
        return

    # Sayı yakala
    match = re.search(r'(\d+)\s?k?', text)
    if not match:
        return

    amount = int(match.group(1))
    if "k" in text:
        amount *= 1000
    if amount <= 0:
        return

    user = message.reply_to_message.from_user if message.reply_to_message else message.from_user
    uid = user.id
    name = user.first_name
    username = user.username if user.username else name

    if uid not in daily_approvals:
        daily_approvals[uid] = {"name": name, "username": username, "total": 0}

    # İptal
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
        mesaj = f"<b>{emojiler} —GÜN SONU— {emojiler}</b>\n\n📊 <b>Günlük Özet</b>\n"
        for data in daily_approvals.values():
            mesaj += f"• {data['name']}: {data['total']:,}\n"

        # Tüm gruplarda gönder
        # Eğer sadece tek grup istiyorsan CHAT_ID ekle
        # await bot.send_message(chat_id=CHAT_ID, text=mesaj, parse_mode='HTML')
        # Şimdilik örnek olarak sadece bir grup gönderecek
        print("Gün sonu mesajı (test):")
        print(mesaj)

        # Günlük verileri sıfırla
        for key in daily_approvals:
            daily_approvals[key]["total"] = 0

# ---------------------
# Botu başlat
# ---------------------
async def main():
    app_bot = ApplicationBuilder().token(TOKEN).build()
    app_bot.add_handler(CommandHandler("rapor", rapor))
    app_bot.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), approval_handler))

    # Background görev
    asyncio.create_task(daily_message())

    await app_bot.start()
    await app_bot.updater.start_polling()
    await app_bot.updater.idle()

asyncio.run(main())
