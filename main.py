import os
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes
import openai

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

openai.api_key = OPENAI_API_KEY

# Admin ID - chỉ những người này mới được dùng GPT-4
ADMIN_IDS = [123456789]  # 👉 Thay bằng Telegram user_id thật của bạn

def get_user_role(user_id: int) -> str:
    return "admin" if user_id in ADMIN_IDS else "user"

async def ask(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.username or update.effective_user.first_name
    role = get_user_role(user_id)
    
    if not context.args:
        await update.message.reply_text("❗ Hãy hỏi như sau: `/ask câu hỏi của bạn`", parse_mode="Markdown")
        return

    prompt = " ".join(context.args)
    model = "gpt-4" if role == "admin" else "gpt-3.5-turbo"

    # Vai trò nhân vật của ChatGPT: Trợ lý vui tính
    system_prompt = "Bạn là một AI hài hước, trả lời như một diễn viên hài."

    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        )
        reply = response.choices[0].message.content

        styled_reply = (
            f"🎭 *{username}* (vai trò: *{role}*) hỏi:
"
            f"🗯️ _{prompt}_

"
            f"🤣 *Trợ lý vui tính trả lời:*
"
            f"{reply}"
        )
        await update.message.reply_text(styled_reply, parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"❌ Lỗi: {str(e)}")

async def role(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    role = get_user_role(user_id)
    await update.message.reply_text(f"👤 Vai trò của bạn là: *{role}*", parse_mode="Markdown")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Xin chào! Gõ `/ask câu hỏi của bạn` để nhận câu trả lời từ trợ lý vui tính 🤡
"
        "🔒 Chỉ *admin* mới được dùng GPT-4.",
        parse_mode="Markdown"
    )

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("role", role))
app.add_handler(CommandHandler("ask", ask))

app.run_polling()
