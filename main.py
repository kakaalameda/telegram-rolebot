import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Bật logging để debug dễ hơn
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))

openai.api_key = OPENAI_API_KEY

ADMIN_IDS = [993884797]  # 👉 Thay bằng Telegram user_id thật của bạn

def get_user_role(user_id: int) -> str:
    return "admin" if user_id in ADMIN_IDS else "user"

def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        logger.info("Unauthorized chat ID: %s", update.effective_chat.id)
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    role = get_user_role(user_id)

    if not context.args:
        await update.message.reply_text("❗ Hãy hỏi như sau: `Sophia câu hỏi của bạn`", parse_mode="Markdown")
        return

    prompt = " ".join(context.args)
    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"

    if role == "admin":
        system_prompt = "Bạn là một phi tần tên Sophia, trả lời như với hoàng thượng."
    else:
        system_prompt = "Bạn là một AI có tên Sophia hài hước, trả lời cùng ngôn ngữ với người dùng như một diễn viên hài Gen Z giới tính nữ."

    logger.info("Sending request to OpenAI: %s", prompt)

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        logger.error("OpenAI error: %s", e)
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        logger.info("Unauthorized message from chat ID: %s", update.effective_chat.id)
        return

    text = update.message.text
    logger.info("Received message: %s", text)

    if not text.lower().startswith("sophia "):
        logger.info("Ignored message (does not start with 'sophia '): %s", text)
        return

    context.args = text.split()[1:]  # Bỏ từ "Sophia"
    await ask(update, context)

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await update.message.reply_text(f"🆔 Chat ID hiện tại là: `{chat_id}`", parse_mode="Markdown")

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
        "👋 Xin chào! Gõ `Sophia câu hỏi của bạn` để nhận câu trả lời từ trợ lý vui tính 🤡\n"
        "🔒 Chỉ *admin* mới được dùng GPT-4.",
        parse_mode="Markdown"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("role", role))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(CommandHandler("getid", getid))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

app.run_polling()
