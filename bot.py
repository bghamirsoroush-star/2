# telegram_bot.py
import asyncio
import logging
import os
from typing import Dict, List, Optional

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    ReplyKeyboardMarkup,
    KeyboardButton,
    ParseMode
)
from telegram.ext import (
    Updater,
    CommandHandler,
    MessageHandler,
    Filters,
    CallbackQueryHandler,
    ConversationHandler,
    CallbackContext
)

from main import SMSBomber, Color

# Enable logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Define states for conversation
PHONE, DELAY, COUNT, CONFIRM = range(4)

# Define bot token
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")

class TelegramBot:
    """Telegram Bot for SMS Bomber"""
    
    def __init__(self):
        self.bomber = SMSBomber()
        self.user_data = {}
    
    def start(self, update: Update, context: CallbackContext) -> int:
        """Start command handler"""
        user = update.effective_user
        keyboard = [
            [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
            [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
        ]
        reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        
        update.message.reply_text(
            f"👋 Hello {user.first_name}!\n\n"
            "Welcome to SMS Bomber Bot 🚀\n\n"
            "This bot can send verification codes to any phone number from multiple services.\n\n"
            "Please select an option:",
            reply_markup=reply_markup
        )
        return PHONE
    
    def about(self, update: Update, context: CallbackContext) -> int:
        """About command handler"""
        update.message.reply_text(
            "📖 *About SMS Bomber Bot*\n\n"
            "Version: 2.0\n"
            "Developer: @YourUsername\n\n"
            "This bot sends verification codes to phone numbers from various Iranian services.\n\n"
            "⚠️ *Disclaimer:* This tool is for educational purposes only. "
            "Do not use for illegal activities or harassment.",
            parse_mode=ParseMode.MARKDOWN
        )
        return PHONE
    
    def settings(self, update: Update, context: CallbackContext) -> int:
        """Settings command handler"""
        user_id = update.effective_user.id
        current_settings = self.user_data.get(user_id, {"delay": 0.1, "count": 1})
        
        keyboard = [
            [InlineKeyboardButton(f"⏱️ Delay: {current_settings['delay']}s", callback_data="settings_delay")],
            [InlineKeyboardButton(f"🔢 Count: {current_settings['count']}", callback_data="settings_count")],
            [InlineKeyboardButton("🔙 Back", callback_data="settings_back")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        update.message.reply_text(
            "⚙️ *Settings*\n\n"
            "Customize your bombing parameters:",
            reply_markup=reply_markup,
            parse_mode=ParseMode.MARKDOWN
        )
        return PHONE
    
    def settings_callback(self, update: Update, context: CallbackContext) -> int:
        """Handle settings callback queries"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {"delay": 0.1, "count": 1}
        
        if query.data == "settings_delay":
            query.edit_message_text(
                "⏱️ *Set Delay*\n\n"
                "Please enter the delay between requests in seconds (0.1-5.0):",
                parse_mode=ParseMode.MARKDOWN
            )
            return DELAY
        elif query.data == "settings_count":
            query.edit_message_text(
                "🔢 *Set Count*\n\n"
                "Please enter how many times to send the codes (1-10):",
                parse_mode=ParseMode.MARKDOWN
            )
            return COUNT
        elif query.data == "settings_back":
            keyboard = [
                [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
                [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            query.edit_message_text(
                "👋 Main Menu\n\n"
                "Please select an option:",
                reply_markup=reply_markup
            )
            return PHONE
    
    def handle_phone(self, update: Update, context: CallbackContext) -> int:
        """Handle phone number input"""
        phone = update.message.text.strip()
        
        # Check if it's a command
        if phone.startswith("/"):
            if phone == "/start":
                return self.start(update, context)
            elif phone == "/about":
                return self.about(update, context)
            elif phone == "/settings":
                return self.settings(update, context)
            else:
                update.message.reply_text("❌ Unknown command. Please try again.")
                return PHONE
        
        # Validate phone number
        try:
            normalized_phone = self.bomber.services[0].normalize_phone(phone)
            user_id = update.effective_user.id
            
            # Store phone in user data
            if user_id not in self.user_data:
                self.user_data[user_id] = {"delay": 0.1, "count": 1}
            self.user_data[user_id]["phone"] = normalized_phone
            
            # Get current settings
            delay = self.user_data[user_id]["delay"]
            count = self.user_data[user_id]["count"]
            
            # Create confirmation keyboard
            keyboard = [
                [InlineKeyboardButton("✅ Yes, send it!", callback_data="confirm_yes")],
                [InlineKeyboardButton("❌ No, cancel", callback_data="confirm_no")],
                [InlineKeyboardButton("⚙️ Change settings", callback_data="confirm_settings")]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            update.message.reply_text(
                f"📱 *Confirm SMS Bombing*\n\n"
                f"Phone: `{normalized_phone}`\n"
                f"Delay: `{delay}s`\n"
                f"Count: `{count}`\n\n"
                f"Are you sure you want to proceed?",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
            return CONFIRM
        except ValueError:
            update.message.reply_text(
                "❌ Invalid phone number format!\n\n"
                "Please enter a valid Iranian phone number:\n"
                "• +989123456789\n"
                "• 09123456789\n"
                "• 9123456789"
            )
            return PHONE
    
    def handle_delay(self, update: Update, context: CallbackContext) -> int:
        """Handle delay input"""
        try:
            delay = float(update.message.text.strip())
            if 0.1 <= delay <= 5.0:
                user_id = update.effective_user.id
                if user_id not in self.user_data:
                    self.user_data[user_id] = {"delay": 0.1, "count": 1}
                self.user_data[user_id]["delay"] = delay
                
                keyboard = [
                    [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
                    [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                update.message.reply_text(
                    f"✅ Delay set to {delay} seconds\n\n"
                    "Main Menu:",
                    reply_markup=reply_markup
                )
                return PHONE
            else:
                update.message.reply_text(
                    "❌ Delay must be between 0.1 and 5.0 seconds. Please try again:"
                )
                return DELAY
        except ValueError:
            update.message.reply_text(
                "❌ Invalid input. Please enter a number between 0.1 and 5.0:"
            )
            return DELAY
    
    def handle_count(self, update: Update, context: CallbackContext) -> int:
        """Handle count input"""
        try:
            count = int(update.message.text.strip())
            if 1 <= count <= 10:
                user_id = update.effective_user.id
                if user_id not in self.user_data:
                    self.user_data[user_id] = {"delay": 0.1, "count": 1}
                self.user_data[user_id]["count"] = count
                
                keyboard = [
                    [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
                    [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
                ]
                reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
                
                update.message.reply_text(
                    f"✅ Count set to {count}\n\n"
                    "Main Menu:",
                    reply_markup=reply_markup
                )
                return PHONE
            else:
                update.message.reply_text(
                    "❌ Count must be between 1 and 10. Please try again:"
                )
                return COUNT
        except ValueError:
            update.message.reply_text(
                "❌ Invalid input. Please enter a number between 1 and 10:"
            )
            return COUNT
    
    def handle_confirm(self, update: Update, context: CallbackContext) -> int:
        """Handle confirmation callback"""
        query = update.callback_query
        query.answer()
        
        user_id = update.effective_user.id
        if user_id not in self.user_data:
            self.user_data[user_id] = {"delay": 0.1, "count": 1}
        
        if query.data == "confirm_yes":
            phone = self.user_data[user_id]["phone"]
            delay = self.user_data[user_id]["delay"]
            count = self.user_data[user_id]["count"]
            
            query.edit_message_text(
                "🚀 *Starting SMS Bombing...*\n\n"
                "Please wait, this may take a moment...",
                parse_mode=ParseMode.MARKDOWN
            )
            
            # Run the bombing in background
            asyncio.create_task(self.run_bombing(update, phone, delay, count))
            return PHONE
        elif query.data == "confirm_no":
            keyboard = [
                [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
                [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            query.edit_message_text(
                "❌ SMS bombing cancelled.\n\n"
                "Main Menu:",
                reply_markup=reply_markup
            )
            return PHONE
        elif query.data == "confirm_settings":
            return self.settings(update, context)
    
    async def run_bombing(self, update: Update, phone: str, delay: float, count: int):
        """Run the SMS bombing process"""
        try:
            await self.bomber.bomb(phone, delay, count)
            
            keyboard = [
                [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
                [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            update.effective_message.reply_text(
                "✅ *SMS bombing completed successfully!*\n\n"
                "Main Menu:",
                reply_markup=reply_markup,
                parse_mode=ParseMode.MARKDOWN
            )
        except Exception as e:
            logger.error(f"Error during bombing: {e}")
            update.effective_message.reply_text(
                f"❌ An error occurred: {str(e)}\n\n"
                "Please try again later."
            )
    
    def handle_message(self, update: Update, context: CallbackContext) -> int:
        """Handle general messages"""
        text = update.message.text.strip()
        
        if text == "📱 Send SMS":
            update.message.reply_text(
                "📱 *Enter Phone Number*\n\n"
                "Please enter the phone number you want to bomb:\n"
                "• +989123456789\n"
                "• 09123456789\n"
                "• 9123456789",
                parse_mode=ParseMode.MARKDOWN
            )
            return PHONE
        elif text == "ℹ️ About":
            return self.about(update, context)
        elif text == "⚙️ Settings":
            return self.settings(update, context)
        elif text == "🔙 Back":
            keyboard = [
                [KeyboardButton("📱 Send SMS"), KeyboardButton("ℹ️ About")],
                [KeyboardButton("⚙️ Settings"), KeyboardButton("🔙 Back")]
            ]
            reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
            
            update.message.reply_text(
                "👋 Main Menu\n\n"
                "Please select an option:",
                reply_markup=reply_markup
            )
            return PHONE
        else:
            return self.handle_phone(update, context)
    
    def error(self, update: Update, context: CallbackContext) -> None:
        """Log errors caused by Updates"""
        logger.warning(f'Update "{update}" caused error "{context.error}"')
    
    def run(self):
        """Run the bot"""
        # Create the Updater and pass it your bot's token.
        updater = Updater(BOT_TOKEN)
        
        # Get the dispatcher to register handlers
        dispatcher = updater.dispatcher
        
        # Add conversation handler
        conv_handler = ConversationHandler(
            entry_points=[CommandHandler('start', self.start)],
            states={
                PHONE: [
                    MessageHandler(Filters.text & ~Filters.command, self.handle_message),
                    CallbackQueryHandler(self.settings_callback, pattern='^settings_')
                ],
                DELAY: [
                    MessageHandler(Filters.text & ~Filters.command, self.handle_delay)
                ],
                COUNT: [
                    MessageHandler(Filters.text & ~Filters.command, self.handle_count)
                ],
                CONFIRM: [
                    CallbackQueryHandler(self.handle_confirm, pattern='^confirm_')
                ]
            },
            fallbacks=[CommandHandler('start', self.start)],
            per_user=True,
            per_chat=True
        )
        
        dispatcher.add_handler(conv_handler)
        
        # Add direct command handlers
        dispatcher.add_handler(CommandHandler('about', self.about))
        dispatcher.add_handler(CommandHandler('settings', self.settings))
        
        # Log all errors
        dispatcher.add_error_handler(self.error)
        
        # Start the Bot
        updater.start_polling()
        
        # Run the bot until you press Ctrl-C
        updater.idle()

if __name__ == '__main__':
    bot = TelegramBot()
    bot.run()
