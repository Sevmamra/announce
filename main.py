import os
import logging
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration from environment variables
BOT_TOKEN = os.getenv('BOT_TOKEN')
YOUR_USER_ID = int(os.getenv('YOUR_USER_ID'))
GROUP_IDS = [int(id.strip()) for id in os.getenv('GROUP_IDS').split(',')]
GROUP_NAMES = os.getenv('GROUP_NAMES').split(',')

# Global variables
broadcast_data = {}
selected_groups = set()  # Moved to top level with proper initialization

def create_group_selection_keyboard():
    """Create inline keyboard with group selection buttons."""
    keyboard = []
    for idx, name in enumerate(GROUP_NAMES):
        button_text = f"{'✅ ' if idx in selected_groups else ''}{name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"select_{idx}")])
    
    broadcast_button_text = "📢 Broadcast to Selected" if selected_groups else "📢 Select groups first"
    keyboard.append([InlineKeyboardButton(broadcast_button_text, callback_data="broadcast_selected")])
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with group selection buttons."""
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access!")
        return

    # Reset selections when starting fresh
    selected_groups.clear()
    
    keyboard = create_group_selection_keyboard()
    await update.message.reply_text(
        "👋 Welcome to Broadcast Bot!\n"
        "📌 Select groups to send message:",
        reply_markup=keyboard
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate broadcast process."""
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access!")
        return

    if not selected_groups:
        await update.message.reply_text("❗ Please select groups first using /start")
        return

    await update.message.reply_text(
        "📝 Please send the content you want to broadcast.\n"
        "It can be text, photo, video, document, sticker, or GIF."
    )
    broadcast_data['awaiting_content'] = True

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all incoming messages for broadcasting."""
    if not broadcast_data.get('awaiting_content') or update.effective_user.id != YOUR_USER_ID:
        return

    # Store the message content based on type
    if update.message.text:
        broadcast_data['content_type'] = 'text'
        broadcast_data['content'] = update.message.text
    elif update.message.photo:
        broadcast_data['content_type'] = 'photo'
        broadcast_data['content'] = update.message.photo[-1].file_id
        broadcast_data['caption'] = update.message.caption
    elif update.message.video:
        broadcast_data['content_type'] = 'video'
        broadcast_data['content'] = update.message.video.file_id
        broadcast_data['caption'] = update.message.caption
    elif update.message.document:
        broadcast_data['content_type'] = 'document'
        broadcast_data['content'] = update.message.document.file_id
        broadcast_data['caption'] = update.message.caption
    elif update.message.sticker:
        broadcast_data['content_type'] = 'sticker'
        broadcast_data['content'] = update.message.sticker.file_id
    elif update.message.animation:
        broadcast_data['content_type'] = 'animation'
        broadcast_data['content'] = update.message.animation.file_id
        broadcast_data['caption'] = update.message.caption
    else:
        await update.message.reply_text("❌ Unsupported media type")
        return

    # Show confirmation with selected groups
    keyboard = create_group_selection_keyboard()
    await update.message.reply_text(
        "✅ Content received!\n"
        f"Selected groups: {len(selected_groups)}\n"
        "Click to modify selection or broadcast:",
        reply_markup=keyboard
    )
    broadcast_data['awaiting_content'] = False

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != YOUR_USER_ID:
        await query.edit_message_text("⛔ Unauthorized access!")
        return

    if query.data.startswith("select_"):
        # Toggle group selection
        group_idx = int(query.data.split("_")[1])
        if group_idx in selected_groups:
            selected_groups.remove(group_idx)
        else:
            selected_groups.add(group_idx)
        
        # Update the message with new selections
        keyboard = create_group_selection_keyboard()
        await query.edit_message_text(
            text=query.message.text,
            reply_markup=keyboard
        )
    elif query.data == "broadcast_selected":
        if not selected_groups:
            await query.answer("❗ Please select at least one group first!", show_alert=True)
            return
        
        await query.edit_message_text("✍️ Please send your message now using /broadcast command")

async def send_broadcast(context: ContextTypes.DEFAULT_TYPE):
    """Send the broadcast to selected groups."""
    success_count = 0
    for group_idx in selected_groups:
        group_id = GROUP_IDS[group_idx]
        group_name = GROUP_NAMES[group_idx]
        
        try:
            if broadcast_data['content_type'] == 'text':
                await context.bot.send_message(
                    chat_id=group_id,
                    text=broadcast_data['content']
                )
            elif broadcast_data['content_type'] == 'photo':
                await context.bot.send_photo(
                    chat_id=group_id,
                    photo=broadcast_data['content'],
                    caption=broadcast_data.get('caption')
                )
            elif broadcast_data['content_type'] == 'video':
                await context.bot.send_video(
                    chat_id=group_id,
                    video=broadcast_data['content'],
                    caption=broadcast_data.get('caption')
                )
            elif broadcast_data['content_type'] == 'document':
                await context.bot.send_document(
                    chat_id=group_id,
                    document=broadcast_data['content'],
                    caption=broadcast_data.get('caption')
                )
            elif broadcast_data['content_type'] == 'sticker':
                await context.bot.send_sticker(
                    chat_id=group_id,
                    sticker=broadcast_data['content']
                )
            elif broadcast_data['content_type'] == 'animation':
                await context.bot.send_animation(
                    chat_id=group_id,
                    animation=broadcast_data['content'],
                    caption=broadcast_data.get('caption')
                )
            success_count += 1
        except Exception as e:
            logger.error(f"Error sending to {group_name} ({group_id}): {e}")
    
    return success_count

def main():
    """Start the bot."""
    # Verify environment variables
    required_vars = ['BOT_TOKEN', 'YOUR_USER_ID', 'GROUP_IDS', 'GROUP_NAMES']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")

    # Create Application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))

    # Start the bot
    logger.info("Bot is running...")
    application.run_polling()

if __name__ == '__main__':
    main()
