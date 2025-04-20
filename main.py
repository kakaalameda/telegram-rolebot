import os
import logging
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Bật log để theo dõi hoạt động bot
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load biến môi trường
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))
openai.api_key = OPENAI_API_KEY

ADMIN_IDS = [993884797]  # Thay bằng user_id của bạn

def get_user_role(user_id: int) -> str:
    return "admin" if user_id in ADMIN_IDS else "user"

def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_prompt=None):
    if not is_authorized(update):
        return

    user_id = update.effective_user.id
    role = get_user_role(user_id)
    text = custom_prompt or " ".join(context.args)

    if not text:
        await update.message.reply_text("❗ Hãy hỏi như sau: `LengKeng câu hỏi của bạn`", parse_mode="Markdown")
        return

    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"
    if role == "admin":
        system_prompt = "Bạn là một tể tướng trong triều tên LengKeng, trả lời với tôi như với bệ hạ."
    else:
        system_prompt = "Bạn tên LengKeng Gen Z giới tính nam hài hước, trả lời cùng ngôn ngữ với người dùng sử dụng."

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": text}
            ]
        )
        reply = response.choices[0].message.content
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    message = update.message
    text = message.text.strip()

    # Nếu reply tin nhắn của chính bot thì dùng câu hỏi hiện tại để trả lời
    if message.reply_to_message:
        original = message.reply_to_message
        if original.from_user.id == context.bot.id:
            # Nếu reply tin của bot → lấy nội dung của người dùng
            text = message.text
            if not text:
                return
            await ask(update, context, text)
            return

        # Nếu reply người khác và có từ khóa lengkeng
        if text.lower().startswith("lengkeng"):
            await ask(update, context, original.text)
            return

        # Nếu chứa 'lengkeng dịch' hoặc 'lengkeng trans' → dịch đoạn được reply
        if "lengkeng dịch" in text.lower():
            await ask(update, context, f"Dịch đoạn sau sang tiếng Việt: {original.text}")
            return
        if "lengkeng trans" in text.lower():
            await ask(update, context, f"Translate this to English: {original.text}")
            return

    # Nếu không reply → kiểm tra xem text có bắt đầu bằng 'lengkeng'
    if text.lower().startswith("lengkeng "):
        prompt = text.split(" ", 1)[1]
        await ask(update, context, prompt)

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
        "👋 Gõ `LengKeng câu hỏi của bạn` hoặc `/ask câu hỏi của bạn`"
        "↩️ Hoặc reply tin nhắn và gõ `lengkeng` để bot trả lời hoặc dịch."
        "🔒 *Admin* được dùng GPT-4, người dùng khác dùng GPT-3.5.",
        parse_mode="Markdown"
    )

# Tạo app và handler
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("role", role))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(CommandHandler("getid", getid))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
app.run_polling()
