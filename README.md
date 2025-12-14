# Budget Bot

A Telegram bot for tracking expenses and managing your budget, built with Python and Supabase.

## Features

- **Track Expenses**: Send messages like `50 groceries` to log expenses
- **Category Selection**: Choose from predefined categories for each expense
- **Daily Budget**: See your remaining daily budget based on your budget period
- **Expense History**: View, edit, and delete past expenses
- **Multi-user Support**: Each user has their own budgets and expenses

## Setup

### 1. Create a Telegram Bot

1. Open Telegram and search for `@BotFather`
2. Send `/newbot` and follow the prompts
3. Copy the bot token provided

### 2. Set Up Supabase

1. Create a free account at [supabase.com](https://supabase.com)
2. Create a new project
3. Go to **SQL Editor** and run the contents of `database/migrations.sql`
4. This will create the required tables (users, budgets, categories, expenses) and seed the default categories
5. Copy your project URL and anon key from **Settings > API**

### 3. Get Your Telegram User ID

**Important:** The bot uses a whitelist system - only authorized users can use it.

To find your Telegram user ID:
1. Open Telegram
2. Search for and message `@userinfobot`
3. It will reply with your user ID (e.g., `123456789`)
4. Copy this number

### 4. Configure Environment

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Then edit `.env` with your actual values:

```
TELEGRAM_BOT_TOKEN=your_bot_token_from_botfather
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key
ADMIN_USER_ID=123456789
```

**Important:** Replace `123456789` with YOUR Telegram user ID (from step 3).

### 5. Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 6. Run the Bot

```bash
python main.py
```

The bot will start polling for messages. You should see:
```
Bot is ready! Press Ctrl+C to stop.
```

## Security Features

- **Database-Based Authorization**: Only authorized users can use the bot
- **Admin System**: The admin (you) can add/remove users without redeploying
- **Auto-Admin Setup**: First time you use the bot, you're automatically registered as admin
- **User Isolation**: Each user's data is completely separate
- **Access Control**: Non-authorized users see their ID and are told to contact you

### Managing Users (Admin Only)

Once you're set up as admin, you can manage users directly through the bot:

- `/adduser <telegram_id>` - Authorize a new user
- `/removeuser <telegram_id>` - Remove a user's access
- `/listusers` - See all authorized users
- `/myid` - Show your Telegram ID (useful for helping others find theirs)

**Example:**
```
You: /adduser 987654321
Bot: ✅ User 987654321 has been authorized! They can now use the bot.
```

**To help someone get their ID:**
1. Tell them to message @userinfobot on Telegram
2. They send you their ID
3. You run `/adduser <their_id>`

## Usage

### Commands

- `/start` - Register and get started
- `/setbudget` - Set a new budget period with amount and date range
- `/budget` - View your current budget status
- `/history` - View your expense history
- `/cancel` - Cancel the current operation

### Adding Expenses

Simply send a message in the format: `<amount> <description>`

Examples:
- `50 groceries`
- `12.50 coffee`
- `100 electricity bill`

The bot will ask you to select a category, then show your updated daily budget.

### Date Format

All dates use **DD-MM-YYYY** format:
- `14-12-2025` for December 14, 2025
- `01-01-2026` for January 1, 2026

## Categories

- 🍔 Food
- 🚗 Transport
- 🛍️ Shopping
- 🎮 Entertainment
- 🏥 Healthcare
- 💰 Bills
- 📚 Education
- ✨ Other

## License

MIT

