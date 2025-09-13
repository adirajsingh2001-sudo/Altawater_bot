# bot.py
import os
import threading
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters
)

# Bot token will come from environment variable set in Railway
BOT_TOKEN = os.environ.get("BOT_TOKEN")
if not BOT_TOKEN:
    raise RuntimeError("BOT_TOKEN environment variable is not set")

# runtime state
DELIVERY_GROUP_ID = None
active_requests = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Altawater Bot. Use /join <flat_number> to register your flat.")

async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /join <flat_number>")
        return
    flat_number = context.args[0]
    context.user_data["flat"] = flat_number
    await update.message.reply_text(f"Registered to flat {flat_number}. Now type 'water' to request water.")

# user types the word "water" (no slash)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().lower()
    if text != "water":
        return
    user_flat = context.user_data.get("flat")
    if not user_flat:
        await update.message.reply_text("You must /join with a flat number first.")
        return
    if user_flat in active_requests:
        await update.message.reply_text("Water already requested for your flat. Please wait for delivery.")
        return

    active_requests[user_flat] = True
    keyboard = [[InlineKeyboardButton("✅ Delivered", callback_data=f"delivered:{user_flat}")]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if DELIVERY_GROUP_ID:
        await context.bot.send_message(
            chat_id=DELIVERY_GROUP_ID,
            text=f"🚰 Water requested for Flat {user_flat}",
            reply_markup=reply_markup,
        )
        await update.message.reply_text("Request sent to delivery team.")
    else:
        await update.message.reply_text("Delivery group not registered yet. Ask admin to run /register_delivery_group in the group.")

async def delivered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    flat_number = query.data.split(":", 1)[1]
    if flat_number in active_requests:
        del active_requests[flat_number]
        await query.edit_message_text(text=f"✅ Water delivered to Flat {flat_number}")
    else:
        await query.edit_message_text(text="No active request found.")

async def register_delivery_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DELIVERY_GROUP_ID
    DELIVERY_GROUP_ID = update.effective_chat.id
    await update.message.reply_text("This group is now registered as the delivery group.")

# tiny web server to keep the app "reachable" for uptime pings
def run_flask():
    app = Flask("keepalive")
    @app.route("/")
    def index():
        return "OK"
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

def main():
    # start flask server in background thread
    t = threading.Thread(target=run_flask)
    t.daemon = True
    t.start()

    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("join", join))
    application.add_handler(CommandHandler("register_delivery_group", register_delivery_group))
    application.add_handler(CallbackQueryHandler(delivered, pattern="^delivered:"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    application.run_polling()

if __name__ == "__main__":
    main()
