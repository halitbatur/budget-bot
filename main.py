"""Budget Bot - Main entry point."""
import asyncio
import logging
import os
from aiohttp import web
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


async def health_check(request):
    """Health check endpoint for Cloud Run."""
    return web.Response(text="OK", status=200)


async def start_web_server():
    """Start aiohttp web server for health checks."""
    app = web.Application()
    app.router.add_get('/', health_check)
    app.router.add_get('/health', health_check)
    
    port = int(os.environ.get('PORT', 8080))
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    
    logger.info(f"Health check server started on port {port}")
    return runner


async def start_bot():
    """Start the Telegram bot."""
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
    
    # Initialize and start polling
    await application.initialize()
    await application.start()
    await application.updater.start_polling(allowed_updates=["message", "callback_query"])
    
    return application


async def main():
    """Run both web server and bot concurrently."""
    # Start web server for health checks
    web_runner = await start_web_server()
    
    # Start Telegram bot
    application = await start_bot()
    
    try:
        # Keep running forever
        while True:
            await asyncio.sleep(1)
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()
        await web_runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())

