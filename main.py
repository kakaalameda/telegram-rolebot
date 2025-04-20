import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load biến môi trường
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))

openai.api_key = OPENAI_API_KEY

ADMIN_IDS = [993884797]  # Thay bằng user_id Telegram thật

def get_user_role(user_id: int) -> str:
    return "admin" if user_id in ADMIN_IDS else "user"

def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("❗ Hãy hỏi như sau: `lengkeng câu hỏi của bạn`", parse_mode="Markdown")
        return

    user_id = update.effective_user.id
    role = get_user_role(user_id)
    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"
    prompt = " ".join(context.args)

    if role == "admin":
        system_prompt = "Bạn là một tể tướng trong triều tên LengKeng, trả lời với tôi như với bệ hạ."
    else:
        system_prompt = "Bạn tên LengKeng Gen Z giới tính nam hài hước, trả lời cùng ngôn ngữ với người dùng sử dụng."

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        await update.message.reply_text(response.choices[0].message.content)
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    message = update.message
    text = message.text or ""
    reply_msg = message.reply_to_message
    reply_text = reply_msg.text if reply_msg else None
    is_reply_to_bot = reply_msg and reply_msg.from_user and reply_msg.from_user.is_bot

    user_id = update.effective_user.id
    role = get_user_role(user_id)
    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"

    # TH1: Reply bot → luôn trả lời nội dung được reply
    if is_reply_to_bot and reply_text:
        context.args = reply_text.split()
        await ask(update, context)
        return

    # TH2: Reply người khác + có từ "lengkeng"
    if reply_msg and not is_reply_to_bot and "lengkeng" in text.lower() and reply_text:
        if "dịch" in text.lower():
            prompt = f"Dịch đoạn sau sang tiếng Việt:\n{reply_text}"
            system_prompt = "Bạn là một trợ lý AI chuyên dịch tiếng Anh sang tiếng Việt."
        elif "trans" in text.lower():
            prompt = f"Translate the following text to English:\n{reply_text}"
            system_prompt = "You are a translation assistant that translates Vietnamese to English clearly."
        else:
            prompt = reply_text
            system_prompt = (
                "Bạn là một tể tướng trong triều tên LengKeng, trả lời với tôi như với bệ hạ."
                if role == "admin"
                else "Bạn tên LengKeng Gen Z giới tính nam hài hước, trả lời cùng ngôn ngữ với người dùng sử dụng."
            )

        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
            )
            await update.message.reply_text(response.choices[0].message.content)
        except Exception as e:
            await update.message.reply_text(f"❌ Lỗi: {str(e)}")
        return

    # TH3: Không reply ai, chỉ gõ lengkeng ...
    if "lengkeng" in text.lower():
        parts = text.lower().split("lengkeng", 1)
        question = parts[1].strip() if len(parts) > 1 else ""
        context.args = question.split()
        await ask(update, context)

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 Chat ID: `{chat_id}`", parse_mode="Markdown")

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    await update.message.reply_text(f"👤 Vai trò của bạn là: *{role}*", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await update.message.reply_text(
        "👋 Gõ `lengkeng câu hỏi của bạn`, hoặc reply câu cần dịch rồi gõ `lengkeng dịch` hay `lengkeng trans`.\n"
        "🔒 Chỉ *admin* mới được dùng GPT-4.",
        parse_mode="Markdown"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("role", role))
app.add_handler(CommandHandler("getid", getid))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

import asyncio
if __name__ == "__main__":
    asyncio.run(app.run_polling())
