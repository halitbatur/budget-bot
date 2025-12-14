import os
from dotenv import load_dotenv

load_dotenv()

# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# Supabase Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Admin Configuration
ADMIN_USER_ID = os.getenv("ADMIN_USER_ID")
if ADMIN_USER_ID:
    ADMIN_USER_ID = int(ADMIN_USER_ID)

# Validate required environment variables
def validate_config():
    """Validate that all required environment variables are set."""
    missing = []
    if not TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not SUPABASE_URL:
        missing.append("SUPABASE_URL")
    if not SUPABASE_KEY:
        missing.append("SUPABASE_KEY")
    if not ADMIN_USER_ID:
        missing.append("ADMIN_USER_ID")
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")

