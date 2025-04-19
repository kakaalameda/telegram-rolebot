import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

ROLES = {
    123456789: "admin",   # Thay bằng ID Telegram thật
    987654321: "mod"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot đã sẵn sàng!")

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = ROLES.get(user_id, "người dùng thường")
    await update.message.reply_text(f"👤 Vai trò của bạn: {role}")

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("role", role))
app.run_polling()