import os
import logging
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, ContextTypes

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Get configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID'))  # Convert to integer
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID'))  # Convert to integer

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward messages from authorized user to group, reject others."""
    if update.message.from_user.id == YOUR_USER_ID:
        try:
            # Forward message to group
            await context.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=f"From Admin: {update.message.text}"
            )
            await update.message.reply_text("✅ Message sent to group!")
        except Exception as e:
            logger.error(f"Error forwarding message: {e}")
            await update.message.reply_text("❌ Failed to send message to group")
    else:
        # Reject unauthorized users
        await update.message.reply_text("⛔ Sorry, you're not authorized to use this bot.")

def main():
    """Start the bot."""
    # Verify environment variables
    required_vars = ['BOT_TOKEN', 'YOUR_USER_ID', 'GROUP_CHAT_ID']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")

    # Create the Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handler for text messages
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    # Start the bot
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
