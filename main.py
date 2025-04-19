import logging
import os
import openai
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load configuration
TELEGRAM_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    raise SystemExit("Missing TELEGRAM_TOKEN or OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY
ADMIN_IDS = {123456789}
ALLOWED_CHAT_ID = None
user_context = {}

def is_authorized_chat(update: Update) -> bool:
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    return not ALLOWED_CHAT_ID or chat_id == ALLOWED_CHAT_ID or user_id in ADMIN_IDS

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Xin chào! Tôi là chatbot sử dụng OpenAI API.\n"
        "Lệnh khả dụng:\n"
        "• /ask <câu hỏi>\n"
        "• /role <vai trò>\n"
        "• /me <thông tin cá nhân>\n"
        "• /getid\n"
        "• /addadmin <user_id> (chỉ admin)"
    )

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Bot chỉ dùng trong nhóm được phép.")
        return
    user_id = update.effective_user.id
    question = " ".join(context.args)
    if not question:
        await update.message.reply_text("❗ Bạn chưa nhập câu hỏi.")
        return

    messages = []
    if user_id in user_context:
        ctx = user_context[user_id]
        sys = ctx.get("system")
        info = ctx.get("user")
        if sys and info:
            messages.append({"role": "system", "content": f"{sys}\nThông tin người dùng: {info}"})
        elif sys:
            messages.append({"role": "system", "content": sys})
        elif info:
            messages.append({"role": "system", "content": f"Thông tin người dùng: {info}"})
    messages.append({"role": "user", "content": question})

    model = "gpt-4" if user_id in ADMIN_IDS else "gpt-3.5-turbo"
    try:
        response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.7)
        answer = response["choices"][0]["message"]["content"]
        await update.message.reply_text(answer)
    except Exception as e:
        logger.error("OpenAI API error: %s", e)
        await update.message.reply_text("❌ Lỗi khi gọi OpenAI.")

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Bot chỉ dùng trong nhóm được phép.")
        return
    user_id = update.effective_user.id
    role_text = " ".join(context.args)
    if not user_context.get(user_id):
        user_context[user_id] = {}
    if role_text:
        user_context[user_id]["system"] = role_text
        await update.message.reply_text(f"✅ Đặt vai trò thành: *{role_text}*", parse_mode="Markdown")
    else:
        user_context[user_id].pop("system", None)
        await update.message.reply_text("🔄 Vai trò bot đặt lại mặc định.")

async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized_chat(update):
        await update.message.reply_text("⚠️ Bot chỉ dùng trong nhóm được phép.")
        return
    user_id = update.effective_user.id
    info_text = " ".join(context.args)
    if not user_context.get(user_id):
        user_context[user_id] = {}
    if info_text:
        user_context[user_id]["user"] = info_text
        await update.message.reply_text("✅ Đã cập nhật thông tin cá nhân.")
    else:
        user_context[user_id].pop("user", None)
        await update.message.reply_text("🔄 Đã xóa thông tin cá nhân.")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"User ID: `{user_id}`\nChat ID: `{chat_id}`", parse_mode="Markdown")

async def addadmin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in ADMIN_IDS:
        await update.message.reply_text("🚫 Bạn không có quyền.")
        return

    target_id = None
    if update.message.reply_to_message:
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        if context.args[0].isdigit():
            target_id = int(context.args[0])
    if not target_id:
        await update.message.reply_text("⚠️ Cách dùng: /addadmin <user_id> hoặc reply tin nhắn.")
        return
    if target_id in ADMIN_IDS:
        await update.message.reply_text(f"ℹ️ `{target_id}` đã là admin.", parse_mode="Markdown")
    else:
        ADMIN_IDS.add(target_id)
        await update.message.reply_text(f"✅ Đã thêm `{target_id}` làm admin.", parse_mode="Markdown")

async def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ask", ask))
    app.add_handler(CommandHandler("role", role))
    app.add_handler(CommandHandler("me", me))
    app.add_handler(CommandHandler("getid", getid))
    app.add_handler(CommandHandler("addadmin", addadmin))
    await app.run_polling()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
