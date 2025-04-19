import logging
import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
BOT_TOKEN = os.getenv("BOT_TOKEN") or os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))

if not BOT_TOKEN or not OPENAI_API_KEY:
    logger.error("Missing BOT_TOKEN or OPENAI_API_KEY")
    raise SystemExit("Missing BOT_TOKEN or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
ADMIN_IDS = {123456789}
user_context = {}

def is_authorized_chat(update: Update) -> bool:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    return ALLOWED_CHAT_ID == 0 or chat_id == ALLOWED_CHAT_ID or user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Xin chào! Đây là bot AI hỗ trợ hỏi đáp. Các lệnh:
"
        "/ask <câu hỏi>
"
        "/role <vai trò bot>
"
        "/me <giới thiệu bạn>
"
        "/getid
"
        "/addadmin <user_id> (chỉ admin)",
        parse_mode="Markdown"
    )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized_chat(update):
        await update.message.reply_text("❌ Bạn không có quyền sử dụng bot này.")
        return

    user_id = update.effective_user.id
    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("❗ Hãy nhập câu hỏi sau /ask.")
        return

    messages = []
    ctx = user_context.get(user_id, {})
    if "system" in ctx and "user" in ctx:
        messages.append({"role": "system", "content": f"{ctx['system']}\nThông tin người dùng: {ctx['user']}"})
    elif "system" in ctx:
        messages.append({"role": "system", "content": ctx["system"]})
    elif "user" in ctx:
        messages.append({"role": "system", "content": f"Thông tin người dùng: {ctx['user']}"})
    messages.append({"role": "user", "content": question})

    model = "gpt-4" if user_id in ADMIN_IDS else "gpt-3.5-turbo"
    try:
        response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.7)
        reply = response.choices[0].message.content
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error("OpenAI error: %s", e)
        await update.message.reply_text("❌ Đã xảy ra lỗi khi gọi OpenAI API.")

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized_chat(update):
        await update.message.reply_text("❌ Bạn không có quyền.")
        return

    user_id = update.effective_user.id
    role_text = " ".join(context.args)
    user_context.setdefault(user_id, {})
    if role_text:
        user_context[user_id]["system"] = role_text
        await update.message.reply_text(f"✅ Đã đặt vai trò: *{role_text}*", parse_mode="Markdown")
    else:
        user_context[user_id].pop("system", None)
        await update.message.reply_text("🔁 Đã xóa vai trò bot.")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized_chat(update):
        await update.message.reply_text("❌ Bạn không có quyền.")
        return

    user_id = update.effective_user.id
    info = " ".join(context.args)
    user_context.setdefault(user_id, {})
    if info:
        user_context[user_id]["user"] = info
        await update.message.reply_text("✅ Đã cập nhật thông tin cá nhân.")
    else:
        user_context[user_id].pop("user", None)
        await update.message.reply_text("🔁 Đã xóa thông tin cá nhân.")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 User ID: `{user_id}`\n💬 Chat ID: `{chat_id}`", parse_mode="Markdown")

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    requester_id = update.effective_user.id
    if requester_id not in ADMIN_IDS:
        await update.message.reply_text("🚫 Bạn không phải admin.")
        return

    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args and context.args[0].isdigit():
        target_id = int(context.args[0])

    if not target_id:
        await update.message.reply_text("❗ Dùng: /addadmin <user_id> hoặc reply tin nhắn.")
    elif target_id in ADMIN_IDS:
        await update.message.reply_text(f"ℹ️ `{target_id}` đã là admin.", parse_mode="Markdown")
    else:
        ADMIN_IDS.add(target_id)
        await update.message.reply_text(f"✅ `{target_id}` đã được thêm làm admin.", parse_mode="Markdown")

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("role", role))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("getid", getid))
    app.add_handler(CommandHandler("addadmin", addadmin))
    app.run_polling()

if __name__ == "__main__":
    main()
