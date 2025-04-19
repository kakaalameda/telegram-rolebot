import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import openai

# Load biến môi trường
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
ALLOWED_CHAT_ID = int(os.getenv("ALLOWED_CHAT_ID", "0"))

openai.api_key = OPENAI_API_KEY

# Danh sách admin
ADMIN_IDS = [123456789]  # 👉 Thay bằng Telegram user_id thật

# Hàm phân quyền
def get_user_role(user_id: int) -> str:
    return "admin" if user_id in ADMIN_IDS else "user"

# Kiểm tra có đúng group/chat_id không
def is_authorized(update: Update) -> bool:
    return update.effective_chat.id == ALLOWED_CHAT_ID

# /ask command
async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    role = get_user_role(user_id)

    if not context.args:
        await safe_reply(update, "❗ Hãy hỏi như sau: /ask câu hỏi của bạn")
        return

    prompt = " ".join(context.args)
    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"

    system_prompt = (
        "Bạn là một trợ lý AI chuyên nghiệp, trả lời ngắn gọn, chính xác và lịch sự như một chuyên gia."
        if role == "admin"
        else "Bạn là một AI có tên Sophia hài hước, trả lời cùng ngôn ngữ với người dùng như một diễn viên hài Gen Z."
    )

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content
        await safe_reply(update, reply)
    except Exception as e:
        await safe_reply(update, f"❌ Lỗi: {str(e)}")

# /getid
async def getid(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await safe_reply(update, f"🆔 Chat ID hiện tại là: `{update.effective_chat.id}`", markdown=True)

# /me
async def me(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    await safe_reply(update, f"🧑‍💻 user_id của bạn là: `{user_id}`", markdown=True)

# /role
async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    await safe_reply(update, f"🧑‍💻 user_id của bạn là: `{user_id}`\n🔐 Vai trò của bạn: *{role}*", markdown=True)

# /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not is_authorized(update):
        return
    await safe_reply(
        update,
        "👋 Xin chào! Gõ `/ask câu hỏi của bạn` để nhận câu trả lời từ trợ lý vui tính 🤡\n🔒 Chỉ *admin* mới được dùng GPT-4.",
        markdown=True
    )

# ✅ Safe reply function
async def safe_reply(update: Update, text: str, markdown=False):
    try:
        parse_mode = "Markdown" if markdown else None
        if update.message:
            await update.message.reply_text(text, parse_mode=parse_mode)
        else:
            await update.effective_chat.send_message(text, parse_mode=parse_mode)
    except Exception as e:
        print(f"[❌] Gửi tin nhắn thất bại: {e}")

# ✅ Error handler
async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    print(f"[⚠️] Lỗi xử lý: {context.error}")

# 🚀 Khởi chạy bot
app = ApplicationBuilder().token(BOT_TOKEN).build()

# Đăng ký các lệnh
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("ask", ask))
app.add_handler(CommandHandler("role", role))
app.add_handler(CommandHandler("getid", getid))
app.add_handler(CommandHandler("me", me))

# Đăng ký xử lý lỗi
app.add_error_handler(error_handler)

# Bắt đầu polling
app.run_polling()
