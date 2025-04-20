import os
import logging
from dotenv import load_dotenv
from telegram import Update, Message
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))

openai.api_key = OPENAI_API_KEY
ADMIN_IDS = [993884797]

# Bộ nhớ hội thoại theo chat_id
chat_memory = {}

def get_user_role(user_id: int) -> str:
    return "admin" if user_id in ADMIN_IDS else "user"

def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID

def get_system_prompt(role: str) -> str:
    return (
        "Bạn là một tể tướng trong triều tên Keng, trả lời với tôi như với bệ hạ và nói bằng giọng Nghệ An."
        if role == "admin"
        else "Bạn tên Keng Gen Z giới tính nam hài hước, trả lời cùng ngôn ngữ với người dùng sử dụng, xưng hô keng với bạn."
    )

async def call_chatgpt_with_memory(chat_id: int, prompt: str, role: str) -> str:
    system_prompt = get_system_prompt(role)
    memory = chat_memory.get(chat_id, [])
    messages = [{"role": "system", "content": system_prompt}] + memory + [{"role": "user", "content": prompt}]

    # Giới hạn độ dài memory
    if len(messages) > 5:
        messages = messages[-5:]

    response = openai.ChatCompletion.create(
        model="gpt-4" if role == "admin" else "gpt-3.5-turbo",
        messages=messages
    )

    reply = response.choices[0].message.content
    # Lưu vào memory
    chat_memory.setdefault(chat_id, []).append({"role": "user", "content": prompt})
    chat_memory[chat_id].append({"role": "assistant", "content": reply})

    return reply

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    msg: Message = update.message
    text = msg.text.strip()
    role = get_user_role(msg.from_user.id)
    reply_msg = msg.reply_to_message
    chat_id = msg.chat_id

    try:
        # Reply chính bot → tiếp tục hội thoại với context
        if reply_msg and reply_msg.from_user and reply_msg.from_user.is_bot:
            reply = await call_chatgpt_with_memory(chat_id, text, role)
            await msg.reply_text(reply, parse_mode="Markdown")
            return

        # Dịch tiếng Việt
        if reply_msg and text.lower() == "dịch":
            prompt = f"Dịch đoạn sau sang tiếng Việt:{reply_msg.text}"
            reply = await call_chatgpt_with_memory(chat_id, prompt, role)
            await msg.reply_text(reply, parse_mode="Markdown")
            return

        # Dịch tiếng Anh
        if reply_msg and text.lower() == "trans":
            prompt = f"Translate this to English:{reply_msg.text}"
            reply = await call_chatgpt_with_memory(chat_id, prompt, role)
            await msg.reply_text(reply, parse_mode="Markdown")
            return

        # Reply người khác + gõ "lengkeng"
        if reply_msg and text.lower() == "lengkeng":
            reply = await call_chatgpt_with_memory(chat_id, reply_msg.text, role)
            await msg.reply_text(reply, parse_mode="Markdown")
            return

        # Gõ "lengkeng ..." trực tiếp
        if text.lower().startswith("lengkeng "):
            prompt = text[9:].strip()
            reply = await call_chatgpt_with_memory(chat_id, prompt, role)
            await msg.reply_text(reply, parse_mode="Markdown")
            return

    except Exception as e:
        await msg.reply_text(f"❌ Lỗi: {str(e)}")

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    role = get_user_role(update.effective_user.id)
    chat_id = update.effective_chat.id
    prompt = " ".join(context.args)
    if not prompt:
        await update.message.reply_text("❗ Hãy gõ `/ask câu hỏi`", parse_mode="Markdown")
        return
    try:
        reply = await call_chatgpt_with_memory(chat_id, prompt, role)
        await update.message.reply_text(reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cid = update.effective_chat.id
    await update.message.reply_text(f"🆔 Chat ID hiện tại là: `{cid}`", parse_mode="Markdown")

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    role = get_user_role(uid)
    await update.message.reply_text(f"👤 Vai trò của bạn là: *{role}*", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🤖 Xin chào! Bạn có thể sử dụng bot như sau:"
        "- `lengkeng câu hỏi` để hỏi"
        "- Reply + `dịch` → dịch sang tiếng Việt"
        "- Reply + `trans` → dịch sang tiếng Anh"
        "- Reply + `lengkeng` → bot trả lời nội dung được reply"
        "- Reply chính bot → bot trả lời mạch lạc theo đoạn trước"
        "🔐 *Admin* dùng GPT-4, người dùng khác dùng GPT-3.5",
        parse_mode="Markdown"
    )

# Khởi tạo bot
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("role", role))
app.add_handler(CommandHandler("getid", getid))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
app.run_polling()
