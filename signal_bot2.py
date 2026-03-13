
import logging
import random
import json
import os
from datetime import datetime, timedelta
from collections import defaultdict
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler

# Logging setup
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

USERS_FILE = "users.json"
SIGNAL_LOG_FILE = "signal_logs.json"
PREMIUM_USERS_FILE = "premium_users.json"
ADMIN_ID = 5470323876
LOGIN_USERNAME = "STB OWNER"
LOGIN_PASSWORD = "@shakwat33s"

USERNAME, PASSWORD = range(2)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_users():
    with open(USERS_FILE, "w") as f:
        json.dump(list(registered_users), f)

def log_signal(user_id, user_name, signals_text):
    log_entry = {
        "user_id": user_id,
        "user_name": user_name,
        "timestamp": datetime.now().isoformat(),
        "signals": signals_text
    }

    logs = []
    if os.path.exists(SIGNAL_LOG_FILE):
        with open(SIGNAL_LOG_FILE, "r") as f:
            logs = json.load(f)

    logs.append(log_entry)

    with open(SIGNAL_LOG_FILE, "w") as f:
        json.dump(logs, f, indent=2)

def load_premium_users():
    if os.path.exists(PREMIUM_USERS_FILE):
        with open(PREMIUM_USERS_FILE, "r") as f:
            return set(json.load(f))
    return set()

def save_premium_users():
    with open(PREMIUM_USERS_FILE, "w") as f:
        json.dump(list(premium_users), f)

registered_users = load_users()
premium_users = load_premium_users()
user_signal_count = defaultdict(lambda: {"count": 0, "date": datetime.now().date()})
DAILY_LIMIT = 5

def generate_signal():
    assets = [
        "BRLUSD", "USDBDT", "USDARS", "USDINR", "USDCOP", "USDEGP",
        "USDIDR", "USDDZD", "USDZAR", "CADCHF", "FB", "USDMXN",
        "INTC", "USDPKR", "USDPHP"
    ]
    directions = ["CALL", "PUT"]
    return f"{random.choice(assets)}-OTC - {random.choice(directions)}"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user_id = update.effective_user.id
    if user_id in registered_users:
        await update.message.reply_text("✅ You are already logged in.\nUse /signal to get signals.")
        return ConversationHandler.END
    await update.message.reply_text("🔐 Please enter your username:")
    return USERNAME

async def ask_password(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["username"] = update.message.text.strip()
    await update.message.reply_text("🔑 Now enter your password:")
    return PASSWORD

async def check_login(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    password = update.message.text.strip()
    username = context.user_data.get("username")
    user_id = update.effective_user.id

    if username == LOGIN_USERNAME and password == LOGIN_PASSWORD:
        registered_users.add(user_id)
        save_users()
        await update.message.reply_text(f"✅ Login successful! Welcome {username}.\nUse /signal to get signals.")
        return ConversationHandler.END
    else:
        await update.message.reply_text("❌ Invalid credentials. Try /start again.")
        return ConversationHandler.END

async def signal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    if user.id not in registered_users:
        await update.message.reply_text("🔒 Please log in first using /start.")
        return

    user_id = user.id
    today = datetime.now().date()
    user_data = user_signal_count[user_id]

    if user_id not in premium_users:
        if user_data["date"] != today:
            user_data["date"] = today
            user_data["count"] = 0

        if user_data["count"] >= DAILY_LIMIT:
            await update.message.reply_text("⚠️ You've reached your daily free signal limit.\nUpgrade to Premium for unlimited access.")
            return

        user_data["count"] += 1

    num_signals = random.randint(5, 10)
    current_time = datetime.now()
    signal_times = sorted([
        current_time + timedelta(minutes=random.randint(1, 60))
        for _ in range(num_signals)
    ])
    signals = f"👤 User: {user.first_name} (ID: {user.id})\n\n📢 *Generated Trading Signals:*\n"
    for signal_time in signal_times:
        signals += f"🕒 {signal_time.strftime('%H:%M')} - {generate_signal()}\n"

    log_signal(user.id, user.first_name, signals)
    await update.message.reply_text(signals, parse_mode="Markdown")

async def make_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to make users premium.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /makepremium <user_id>")
        return

    try:
        target_id = int(context.args[0])
        premium_users.add(target_id)
        save_premium_users()
        await update.message.reply_text(f"✅ User {target_id} is now Premium.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def remove_premium(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to remove premium.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Usage: /removepremium <user_id>")
        return

    try:
        target_id = int(context.args[0])
        if target_id in premium_users:
            premium_users.remove(target_id)
            save_premium_users()
            await update.message.reply_text(f"🧾 User {target_id} is no longer Premium.")
        else:
            await update.message.reply_text(f"ℹ️ User {target_id} was not Premium.")
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID.")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to use this command.")
        return

    if not context.args:
        await update.message.reply_text("ℹ️ Please provide a message to broadcast. Example: /broadcast Hello users!")
        return

    message = " ".join(context.args)
    count = 0
    for uid in registered_users:
        try:
            await context.bot.send_message(chat_id=uid, text=f"📢 {message}")
            count += 1
        except Exception as e:
            logging.warning(f"Failed to send to {uid}: {e}")

    await update.message.reply_text(f"✅ Message sent to {count} users.")

async def users(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to view users.")
        return

    if not registered_users:
        await update.message.reply_text("📭 No users registered yet.")
        return

    user_list = "👥 Registered Users:\n"
    for uid in registered_users:
        try:
            user_obj = await context.bot.get_chat(uid)
            user_list += f"- {user_obj.first_name} (ID: {uid})\n"
        except:
            user_list += f"- Unknown User (ID: {uid})\n"

    await update.message.reply_text(user_list)

async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to view logs.")
        return

    if not os.path.exists(SIGNAL_LOG_FILE):
        await update.message.reply_text("📭 No logs found.")
        return

    with open(SIGNAL_LOG_FILE, "r") as f:
        logs = json.load(f)

    if not logs:
        await update.message.reply_text("📭 No logs found.")
        return

    for log in logs:
        log_text = (
            f"👤 {log['user_name']} (ID: {log['user_id']})\n"
            f"🕒 {log['timestamp']}\n"
            f"🧾 Signals:\n{log['signals']}"
        )
        try:
            await update.message.reply_text(log_text[:4000])
        except:
            continue

async def clear_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    if user_id != ADMIN_ID:
        await update.message.reply_text("❌ You are not authorized to clear logs.")
        return

    if os.path.exists(SIGNAL_LOG_FILE):
        os.remove(SIGNAL_LOG_FILE)
        await update.message.reply_text("✅ All logs have been cleared.")
    else:
        await update.message.reply_text("📭 No logs to clear.")

def main():
    TOKEN = "7875006076:AAGLCw9oI_O-Fr_ZP8fMSzxq5-b99OXJQ_4"
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            USERNAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_password)],
            PASSWORD: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_login)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.add_handler(CommandHandler("signal", signal))
    app.add_handler(CommandHandler("broadcast", broadcast))
    app.add_handler(CommandHandler("users", users))
    app.add_handler(CommandHandler("logs", logs))
    app.add_handler(CommandHandler("clearlogs", clear_logs))
    app.add_handler(CommandHandler("makepremium", make_premium))
    app.add_handler(CommandHandler("removepremium", remove_premium))

    print("📡 Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
