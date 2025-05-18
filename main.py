import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Your Telegram user ID (replace with your actual ID)
YOUR_USER_ID = 6567162029  # Change this to your Telegram user ID
GROUP_CHAT_ID = -1002359059147  # Change this to your group's chat ID

async def forward_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Forward messages from you to the group, reject others."""
    if update.message.from_user.id == YOUR_USER_ID:
        # Forward your message to the group
        await context.bot.send_message(
            chat_id=GROUP_CHAT_ID,
            text=update.message.text
        )
        await update.message.reply_text("Message sent to group!")
    else:
        # Reject messages from others
        await update.message.reply_text("Sorry, you're not authorized to use this bot.")

def main():
    """Start the bot."""
    # Create the Application
    application = Application.builder().token("YOUR_BOT_TOKEN").build()  # Replace with your bot token

    # Add handlers
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, forward_message))

    # Run the bot
    application.run_polling()

if __name__ == '__main__':
    main()
