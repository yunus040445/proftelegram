from telegram import Update, Bot
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters
import asyncio
import re
import random

TOKEN = "8534122580:AAGRW6bWUnyHIYH7Xk1CvezfFOedmXp826g"
bot = Bot(token=TOKEN)

daily_approvals = {}
emoji_sets = ["💸💯👑", "✨💵🎉", "💎🤑🔥", "💰💎💯"]
BLACKLIST = ["yat yok", "red", "onay yok", "yok"]

async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member = await context.bot.get_chat_member(update.effective_chat.id, update.effective_user.id)
    return member.status in ["administrator", "creator"]

async def rapor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.message.from_user
    if not await is_admin(update, context):
        await update.message.reply_text("❌ Sadece admin kullanabilir.")
        return
    args = context.args
    if not args:
        await update.message.reply_text("⚠️ Kullanıcı adı gir: /rapor @kullanici")
        return
    username = args[0].lstrip("@")
    for data in daily_approvals.values():
        if data["username"].lower() == username.lower():
            await update.message.reply_text(f"📊 {data['name']} – Bugün\nToplam Onay: {data['total']:,}")
            return
    await update.message.reply_text("⚠️ Bu kullanıcıya ait veri yok.")

async def approval_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return
    if not await is_admin(update, context):
        return
    text = message.text.lower()
    if any(word in text and "iptal" not in text for word in BLACKLIST):
        return
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
    if "iptal" in text:
        daily_approvals[uid]["total"] -= amount
        if daily_approvals[uid]["total"] < 0:
            daily_approvals[uid]["total"] = 0
        await message.reply_text(f"↩️ {name} için {amount:,} geri alındı\n📊 Güncel toplam: {daily_approvals[uid]['total']:,}")
        return
    daily_approvals[uid]["total"] += amount
    await message.reply_text(f"✅ {name} için {amount:,} onay kaydedildi\n📊 Bugünkü toplam: {daily_approvals[uid]['total']:,}")

def run_bot():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("rapor", rapor))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), approval_handler))
    app.run_polling()

if __name__ == "__main__":
    run_bot()
