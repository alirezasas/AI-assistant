import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

# === Configuration ===
TELEGRAM_TOKEN = "8004274048:AAGNnOBdmpQwLKXHsMvM5-EfeHetPwaa54E"
OPENROUTER_API_KEY = "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"
MODEL = "meta-llama/llama-3-8b-instruct"
CHANNEL_USERNAME = "@Koinophobica"

# === Headers for OpenRouter ===
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "HTTP-Referer": "https://t.me/KoinophobicaBot",
    "X-Title": "TelegramAIChatBot"
}

# === Memory for user modes and conversation histories ===
user_modes = {}
user_histories = {}
DEFAULT_MODE = "casual"

# === Check if user is a channel member ===
async def is_member(user_id, context):
    try:
        member = await context.bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        return member.status in ["member", "administrator", "creator"]
    except:
        return False

# === Join channel button ===
def join_channel_button():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("Join Channel", url=f"https://t.me/{CHANNEL_USERNAME.strip('@')}")]
    ])

# === /start command ===
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_member(user_id, context):
        await update.message.reply_text(
            f"You must join our channel to use this bot!",
            reply_markup=join_channel_button()
        )
        return

    await update.message.reply_text(
        f"Welcome! I'm your smart assistant.\n\n"
        f"Default mode: *{DEFAULT_MODE.capitalize()}*\n"
        f"Use /help to see all commands.",
        parse_mode="Markdown"
    )

# === /help command ===
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """
Available Commands:
/start - Start the bot
/help - Show this help menu
/code - Programming assistant mode
/study - Study and learning mode
/casual - Friendly and fun chat mode
/mode - Show your current mode
/reset - Reset conversation memory and mode
"""
    await update.message.reply_text(help_text.strip(), parse_mode="Markdown")

# === /mode command ===
async def show_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    mode = user_modes.get(user_id, DEFAULT_MODE)
    await update.message.reply_text(f"Your current mode is: *{mode.capitalize()}*", parse_mode="Markdown")

# === /reset command ===
async def reset_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id in user_histories:
        user_histories[user_id] = []
    user_modes[user_id] = DEFAULT_MODE
    await update.message.reply_text(f"Conversation memory cleared and mode reset to *{DEFAULT_MODE.capitalize()}*.", parse_mode="Markdown")

# === Set mode helper ===
async def set_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, mode: str, description: str):
    user_id = update.effective_user.id
    user_modes[user_id] = mode
    await update.message.reply_text(f"Switched to *{description}* mode.", parse_mode="Markdown")

# === Mode commands ===
async def code_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mode(update, context, "code", "Programming Assistant")

async def study_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mode(update, context, "study", "Study Helper")

async def casual_mode(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await set_mode(update, context, "casual", "Casual Chat")

# === Main message handler ===
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await is_member(user_id, context):
        await update.message.reply_text(
            f"You must join our channel to use this bot!",
            reply_markup=join_channel_button()
        )
        return

    user_msg = update.message.text
    mode = user_modes.get(user_id, DEFAULT_MODE)

    system_prompt = {
        "code": "You are a helpful and precise programming assistant. Provide clean, well-explained code.",
        "study": "You are a supportive study coach who explains concepts clearly and asks helpful questions.",
        "casual": "You are a witty, friendly companion who chats casually and warmly.",
    }.get(mode, "You are a helpful assistant.")

    if user_id not in user_histories:
        user_histories[user_id] = []

    if not user_histories[user_id]:
        user_histories[user_id].append({"role": "system", "content": system_prompt})

    user_histories[user_id].append({"role": "user", "content": user_msg})

    # Show typing...
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action=ChatAction.TYPING)

    payload = {
        "model": MODEL,
        "messages": user_histories[user_id]
    }

    try:
        response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=HEADERS, json=payload)
        reply = response.json()['choices'][0]['message']['content']
        user_histories[user_id].append({"role": "assistant", "content": reply})
        reply += f"\n\n— Powered by {CHANNEL_USERNAME}"
    except Exception as e:
        reply = f"Error: {str(e)}"

    await update.message.reply_text(reply, parse_mode="Markdown")

# === Run the Bot ===
app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("help", help_command))
app.add_handler(CommandHandler("code", code_mode))
app.add_handler(CommandHandler("study", study_mode))
app.add_handler(CommandHandler("casual", casual_mode))
app.add_handler(CommandHandler("mode", show_mode))
app.add_handler(CommandHandler("reset", reset_mode))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.run_polling()