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

# Global variables to store state
broadcast_content = {}
selected_groups = set()

def create_group_selection_keyboard():
    """Create inline keyboard with group selection buttons."""
    keyboard = []
    for idx, name in enumerate(GROUP_NAMES):
        button_text = f"{'✅ ' if idx in selected_groups else ''}{name}"
        keyboard.append([InlineKeyboardButton(button_text, callback_data=f"group_{idx}")])
    
    if broadcast_content.get('content'):
        keyboard.append([InlineKeyboardButton("🚀 BROADCAST NOW", callback_data="do_broadcast")])
    else:
        keyboard.append([InlineKeyboardButton("📝 SEND CONTENT FIRST", callback_data="need_content")])
    
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send welcome message with group selection buttons."""
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access!")
        return

    # Reset previous selections
    selected_groups.clear()
    
    await update.message.reply_text(
        "📌 *GROUP BROADCAST TOOL*\n"
        "Select target groups below:",
        reply_markup=create_group_selection_keyboard(),
        parse_mode='Markdown'
    )

async def broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Initiate broadcast content collection."""
    if update.effective_user.id != YOUR_USER_ID:
        await update.message.reply_text("⛔ Unauthorized access!")
        return

    if not selected_groups:
        await update.message.reply_text(
            "❗ *Please select groups first!*\n"
            "Use /start to choose target groups",
            parse_mode='Markdown'
        )
        return

    await update.message.reply_text(
        "📤 *Ready to broadcast!*\n"
        "Send me the content now:\n"
        "- Text\n- Photo\n- Video\n- Document\n- Sticker\n- GIF",
        parse_mode='Markdown'
    )

async def handle_content(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle incoming broadcast content."""
    if update.effective_user.id != YOUR_USER_ID:
        return

    # Store content based on type
    if update.message.text:
        broadcast_content['type'] = 'text'
        broadcast_content['data'] = update.message.text
    elif update.message.photo:
        broadcast_content['type'] = 'photo'
        broadcast_content['data'] = update.message.photo[-1].file_id
        broadcast_content['caption'] = update.message.caption
    elif update.message.video:
        broadcast_content['type'] = 'video'
        broadcast_content['data'] = update.message.video.file_id
        broadcast_content['caption'] = update.message.caption
    elif update.message.document:
        broadcast_content['type'] = 'document'
        broadcast_content['data'] = update.message.document.file_id
        broadcast_content['caption'] = update.message.caption
    elif update.message.sticker:
        broadcast_content['type'] = 'sticker'
        broadcast_content['data'] = update.message.sticker.file_id
    elif update.message.animation:
        broadcast_content['type'] = 'animation'
        broadcast_content['data'] = update.message.animation.file_id
        broadcast_content['caption'] = update.message.caption
    else:
        await update.message.reply_text("❌ Unsupported media type")
        return

    # Show confirmation with selected groups
    await update.message.reply_text(
        f"✅ *Content received!*\n"
        f"Selected groups: {len(selected_groups)}\n"
        "Click below to broadcast:",
        reply_markup=create_group_selection_keyboard(),
        parse_mode='Markdown'
    )

async def handle_button_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button interactions."""
    query = update.callback_query
    await query.answer()

    if query.from_user.id != YOUR_USER_ID:
        await query.edit_message_text("⛔ Unauthorized access!")
        return

    if query.data.startswith("group_"):
        # Toggle group selection
        group_idx = int(query.data.split("_")[1])
        if group_idx in selected_groups:
            selected_groups.remove(group_idx)
        else:
            selected_groups.add(group_idx)
        
        # Update the message
        await query.edit_message_text(
            text=query.message.text,
            reply_markup=create_group_selection_keyboard()
        )
    
    elif query.data == "do_broadcast":
        if not selected_groups:
            await query.answer("❗ No groups selected!", show_alert=True)
            return
            
        if not broadcast_content:
            await query.answer("❗ No content to send!", show_alert=True)
            return

        # Perform the broadcast
        success = 0
        total = len(selected_groups)
        
        await query.edit_message_text(f"📤 Broadcasting to {total} groups...")
        
        for group_idx in selected_groups:
            group_id = GROUP_IDS[group_idx]
            try:
                if broadcast_content['type'] == 'text':
                    await context.bot.send_message(
                        chat_id=group_id,
                        text=broadcast_content['data']
                    )
                elif broadcast_content['type'] == 'photo':
                    await context.bot.send_photo(
                        chat_id=group_id,
                        photo=broadcast_content['data'],
                        caption=broadcast_content.get('caption')
                    )
                elif broadcast_content['type'] == 'video':
                    await context.bot.send_video(
                        chat_id=group_id,
                        video=broadcast_content['data'],
                        caption=broadcast_content.get('caption')
                    )
                elif broadcast_content['type'] == 'document':
                    await context.bot.send_document(
                        chat_id=group_id,
                        document=broadcast_content['data'],
                        caption=broadcast_content.get('caption')
                    )
                elif broadcast_content['type'] == 'sticker':
                    await context.bot.send_sticker(
                        chat_id=group_id,
                        sticker=broadcast_content['data']
                    )
                elif broadcast_content['type'] == 'animation':
                    await context.bot.send_animation(
                        chat_id=group_id,
                        animation=broadcast_content['data'],
                        caption=broadcast_content.get('caption')
                    )
                success += 1
            except Exception as e:
                logger.error(f"Failed to send to group {group_id}: {e}")
        
        # Send final report
        await query.edit_message_text(
            f"✅ *Broadcast Complete!*\n"
            f"• Success: {success}\n"
            f"• Failed: {total - success}\n"
            f"\nUse /start to send again",
            parse_mode='Markdown'
        )
        
        # Reset for next broadcast
        selected_groups.clear()
        broadcast_content.clear()
    
    elif query.data == "need_content":
        await query.answer("❗ Please send content using /broadcast first", show_alert=True)

def main():
    """Start the bot."""
    # Verify required environment variables
    required_vars = ['BOT_TOKEN', 'YOUR_USER_ID', 'GROUP_IDS', 'GROUP_NAMES']
    for var in required_vars:
        if not os.getenv(var):
            raise ValueError(f"Missing required environment variable: {var}")

    # Create bot application
    application = Application.builder().token(BOT_TOKEN).build()

    # Add handlers
    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('broadcast', broadcast_command))
    application.add_handler(MessageHandler(filters.ALL & ~filters.COMMAND, handle_content))
    application.add_handler(CallbackQueryHandler(handle_button_click))

    # Start the bot
    logger.info("Bot is running and ready...")
    application.run_polling()

if __name__ == '__main__':
    main()
