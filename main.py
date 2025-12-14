"""Budget Bot - Main entry point."""
import logging
from telegram.ext import Application, CommandHandler, CallbackQueryHandler

from config import TELEGRAM_BOT_TOKEN, validate_config
from bot.handlers import (
    start_command,
    budget_command,
    history_command,
    handle_history_navigation,
    handle_unknown_message,
    adduser_command,
    removeuser_command,
    listusers_command,
    myid_command,
    build_expense_conversation_handler,
    build_budget_conversation_handler,
    build_edit_conversation_handler,
    build_delete_conversation_handler,
)

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


def main():
    """Start the bot."""
    # Validate configuration
    validate_config()
    
    logger.info("Starting Budget Bot...")
    
    # Create application
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("budget", budget_command))
    application.add_handler(CommandHandler("history", history_command))
    
    # Add admin command handlers
    application.add_handler(CommandHandler("adduser", adduser_command))
    application.add_handler(CommandHandler("removeuser", removeuser_command))
    application.add_handler(CommandHandler("listusers", listusers_command))
    application.add_handler(CommandHandler("myid", myid_command))
    
    # Add conversation handlers (order matters!)
    application.add_handler(build_budget_conversation_handler())
    application.add_handler(build_edit_conversation_handler())
    application.add_handler(build_delete_conversation_handler())
    application.add_handler(build_expense_conversation_handler())
    
    # Add callback handler for history navigation
    application.add_handler(CallbackQueryHandler(handle_history_navigation, pattern=r'^(history_page_\d+|noop)$'))
    
    logger.info("Bot is ready! Press Ctrl+C to stop.")
    
    # Start polling
    application.run_polling(allowed_updates=["message", "callback_query"])


if __name__ == "__main__":
    main()

