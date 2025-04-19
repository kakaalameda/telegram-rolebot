#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import logging
import os
import openai
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Configure logging for debugging and clarity
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load configuration from environment variables (recommended for security)
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not TELEGRAM_TOKEN or not OPENAI_API_KEY:
    logger.error("TELEGRAM_TOKEN or OPENAI_API_KEY is not set. Please configure them.")
    # Alternatively, you can set the tokens directly here:
    # TELEGRAM_TOKEN = "YOUR-TELEGRAM-BOT-TOKEN"
    # OPENAI_API_KEY = "YOUR-OPENAI-API-KEY"
    raise SystemExit("Missing TELEGRAM_TOKEN or OPENAI_API_KEY configuration.")

openai.api_key = OPENAI_API_KEY

# Admin and chat configuration
ADMIN_IDS = {123456789}  # Initial admin user IDs; replace with actual ID(s)
ALLOWED_CHAT_ID = None   # Set to a specific chat ID to restrict the bot to that chat (or leave None for no restriction)

# In-memory storage for user-specific context (role and personal info)
user_context = {}  # e.g., user_context[user_id] = {"system": "...", "user": "..."}

def is_authorized_chat(update: Update) -> bool:
    """Check if the update is from an allowed chat or an admin user."""
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    if ALLOWED_CHAT_ID and chat_id != ALLOWED_CHAT_ID and user_id not in ADMIN_IDS:
        return False
    return True

def start(update: Update, context: CallbackContext) -> None:
    """Send a welcome message and usage instructions on /start."""
    # We allow /start in any chat to let users see instructions
    welcome_text = (
        "Xin chào! Tôi là chatbot sử dụng OpenAI API.\n"
        "Các lệnh khả dụng:\n"
        "• /ask <câu hỏi> – Đặt câu hỏi cho tôi.\n"
        "• /role <vai trò> – Đặt vai trò cho bot (ví dụ: giáo viên, bác sĩ...).\n"
        "• /me <thông tin> – Cung cấp thông tin về bạn (cho ngữ cảnh hỏi đáp).\n"
        "• /getid – Lấy ID Telegram của bạn (hoặc nhóm hiện tại).\n"
        "• /addadmin <user_id> – (Chỉ admin) Thêm một admin mới bằng ID."
    )
    update.message.reply_text(welcome_text)

def ask(update: Update, context: CallbackContext) -> None:
    """Handle the /ask command to query the OpenAI chat model."""
    if not is_authorized_chat(update):
        update.message.reply_text("⚠️ Bot này chỉ được sử dụng trong nhóm được chỉ định.")
        return
    user_id = update.effective_user.id
    question = " ".join(context.args)
    if not question:
        update.message.reply_text("Vui lòng nhập câu hỏi sau lệnh /ask.")
        return

    # Build the messages payload for OpenAI, including context if available
    messages = []
    if user_id in user_context and "system" in user_context[user_id]:
        # Include the system role/persona if the user set one
        system_role = user_context[user_id]["system"]
        if "user" in user_context[user_id]:
            # Include user's personal info in the system message as context
            user_info = user_context[user_id]["user"]
            system_content = f"{system_role}\nThông tin người dùng: {user_info}"
        else:
            system_content = system_role
        messages.append({"role": "system", "content": system_content})
    elif user_id in user_context and "user" in user_context[user_id]:
        # If only user info is set (and no system role), include it as system context
        user_info = user_context[user_id]["user"]
        messages.append({"role": "system", "content": f"Thông tin người dùng: {user_info}"})
    # Add the user's actual question
    messages.append({"role": "user", "content": question})

    # Select model based on user permission (GPT-4 for admins, GPT-3.5 for others)
    model = "gpt-3.5-turbo"
    if user_id in ADMIN_IDS:
        model = "gpt-4"
    try:
        response = openai.ChatCompletion.create(model=model, messages=messages, temperature=0.7)
        answer = response["choices"][0]["message"]["content"]
        update.message.reply_text(answer)
    except Exception as e:
        logger.error("Error while calling OpenAI API: %s", e)
        update.message.reply_text("❌ Đã xảy ra lỗi khi gọi OpenAI. Vui lòng thử lại sau.")

def role(update: Update, context: CallbackContext) -> None:
    """Set or clear the system role (persona) for the bot."""
    if not is_authorized_chat(update):
        update.message.reply_text("⚠️ Bot này chỉ được sử dụng trong nhóm được chỉ định.")
        return
    user_id = update.effective_user.id
    role_text = " ".join(context.args)
    if not role_text:
        # Clear the role if no text is given
        if user_id in user_context and "system" in user_context[user_id]:
            user_context[user_id].pop("system", None)
        update.message.reply_text("🔄 Vai trò của bot đã được đặt về mặc định.")
    else:
        # Set the new role/persona for this user
        if user_id not in user_context:
            user_context[user_id] = {}
        user_context[user_id]["system"] = role_text
        update.message.reply_text(f"✅ Đã đặt vai trò bot thành: *{role_text}*.", parse_mode="Markdown")

def me(update: Update, context: CallbackContext) -> None:
    """Set or clear the user's personal info for context."""
    if not is_authorized_chat(update):
        update.message.reply_text("⚠️ Bot này chỉ được sử dụng trong nhóm được chỉ định.")
        return
    user_id = update.effective_user.id
    info_text = " ".join(context.args)
    if not info_text:
        # Clear personal info if no text provided
        if user_id in user_context and "user" in user_context[user_id]:
            user_context[user_id].pop("user", None)
        update.message.reply_text("🔄 Đã xóa thông tin cá nhân của bạn.")
    else:
        if user_id not in user_context:
            user_context[user_id] = {}
        user_context[user_id]["user"] = info_text
        update.message.reply_text("✅ Thông tin cá nhân của bạn đã được cập nhật.")

def getid(update: Update, context: CallbackContext) -> None:
    """Respond with the user's ID and chat ID (for configuration)."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    update.message.reply_text(f"User ID của bạn: `{user_id}`\nChat ID: `{chat_id}`", parse_mode="Markdown")

def addadmin(update: Update, context: CallbackContext) -> None:
    """Add a new admin by user ID (admin-only command)."""
    invoking_user = update.effective_user.id
    if invoking_user not in ADMIN_IDS:
        update.message.reply_text("🚫 Bạn không có quyền sử dụng lệnh này.")
        return

    # Determine target user ID from reply or argument
    target_id = None
    if update.message.reply_to_message:
        # If replying to someone's message, use that user's id
        target_id = update.message.reply_to_message.from_user.id
    elif context.args:
        user_id_str = context.args[0]
        if not user_id_str.isdigit():
            update.message.reply_text("❗ Vui lòng cung cấp ID người dùng hợp lệ (số).")
            return
        target_id = int(user_id_str)
    else:
        update.message.reply_text("Cách dùng: `/addadmin <ID người dùng>`\n(Bạn cũng có thể reply tin nhắn của người cần thêm quyền admin.)", parse_mode="Markdown")
        return

    if target_id is None:
        update.message.reply_text("❌ Không xác định được người dùng để thêm admin.")
    elif target_id in ADMIN_IDS:
        update.message.reply_text(f"ℹ️ Người dùng `{target_id}` đã có quyền admin.", parse_mode="Markdown")
    else:
        ADMIN_IDS.add(target_id)
        update.message.reply_text(f"✅ Đã thêm người dùng `{target_id}` làm admin.", parse_mode="Markdown")

def main() -> None:
    """Start the bot and register command handlers."""
    updater = Updater(TELEGRAM_TOKEN, use_context=True)
    dp = updater.dispatcher

    # Register command handlers for all commands
    dp.add_handler(CommandHandler("start", start))
    dp.add_handler(CommandHandler("ask", ask))
    dp.add_handler(CommandHandler("role", role))
    dp.add_handler(CommandHandler("me", me))
    dp.add_handler(CommandHandler("getid", getid))
    dp.add_handler(CommandHandler("addadmin", addadmin))

    # Start polling Telegram for updates
    updater.start_polling()
    logger.info("🤖 Bot has started. Waiting for commands...")
    updater.idle()

if __name__ == "__main__":
    main()
