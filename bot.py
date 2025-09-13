from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# Replace with your BotFather token
BOT_TOKEN = " "

# Global variables
DELIVERY_GROUP_ID = None
active_requests = {}

# Start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I am Altawater Bot. Use /join <flat_number> to register your flat.")

# Join flat
async def join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) != 1:
        await update.message.reply_text("Usage: /join <flat_number>")
        return
    flat_number = context.args[0]
    context.user_data["flat"] = flat_number
    await update.message.reply_text(f"Registered to flat {flat_number}. Now type 'water' to request water.")

# Handle normal messages (like typing 'water')
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.lower()
    if text == "water":
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
            await update.message.reply_text("Delivery group not registered yet.")

# Mark delivered
async def delivered(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    flat_number = query.data.split(":")[1]

    if flat_number in active_requests:
        del active_requests[flat_number]
        await query.edit_message_text(text=f"✅ Water delivered to Flat {flat_number}")
    else:
        await query.edit_message_text(text="No active request found.")

# Register delivery group
async def register_delivery_group(update: Update, context: ContextTypes.DEFAULT_TYPE):
    global DELIVERY_GROUP_ID
    DELIVERY_GROUP_ID = update.effective_chat.id
    await update.message.reply_text("This group is now registered as the delivery group.")

# Main function
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    # Handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("join", join))
    app.add_handler(CommandHandler("register_delivery_group", register_delivery_group))
    app.add_handler(CallbackQueryHandler(delivered, pattern="^delivered:"))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()

