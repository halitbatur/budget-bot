"""Telegram bot handlers for commands and messages."""
from datetime import date, datetime
from functools import wraps
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from bot.states import ConversationState
from bot.keyboards import (
    build_category_keyboard,
    build_expense_actions_keyboard,
    build_edit_options_keyboard,
    build_delete_confirmation_keyboard,
    build_history_navigation_keyboard,
)
from config import ADMIN_USER_ID
from database import queries
from services.expense_parser import parse_expense, is_expense_message, ExpenseParseError
from services.budget_calculator import format_budget_status, format_expense_confirmation
from services.user_service import (
    get_or_create_user_from_telegram,
    get_user_budget_status,
    create_user_budget,
)


# ============== Helper Functions ==============

def authorized_only(func):
    """Decorator to restrict access to authorized users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is authorized in database
        if not queries.is_user_authorized(user_id):
            # Special case: if this is the admin user and they're not in DB yet, auto-add them
            if user_id == ADMIN_USER_ID:
                queries.add_authorized_user(
                    telegram_user_id=user_id,
                    username=update.effective_user.username,
                    first_name=update.effective_user.first_name,
                    is_admin=True,
                    added_by_telegram_id=user_id
                )
            else:
                await update.effective_message.reply_text(
                    "🚫 *Access Denied*\n\n"
                    "This bot is private and requires authorization.\n"
                    f"Your Telegram ID: `{user_id}`\n\n"
                    "Contact the bot owner to request access.",
                    parse_mode="Markdown"
                )
                return ConversationHandler.END if "conversation" in func.__name__ else None
        
        return await func(update, context, *args, **kwargs)
    return wrapper


def admin_only(func):
    """Decorator to restrict access to admin users only."""
    @wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # Check if user is admin
        if not queries.is_user_admin(user_id) and user_id != ADMIN_USER_ID:
            await update.effective_message.reply_text(
                "🚫 *Admin Only*\n\n"
                "This command is only available to administrators.",
                parse_mode="Markdown"
            )
            return None
        
        return await func(update, context, *args, **kwargs)
    return wrapper


async def get_user(update: Update) -> dict:
    """Get or create user from the update."""
    return get_or_create_user_from_telegram(update.effective_user)


def parse_date(date_str: str, date_format: str = "%d-%m-%Y") -> date:
    """Parse a date string in DD-MM-YYYY format.
    
    Args:
        date_str: Date string to parse.
        date_format: Format string (default: DD-MM-YYYY).
    
    Returns:
        Parsed date object.
    
    Raises:
        ValueError: If date format is invalid.
    """
    return datetime.strptime(date_str, date_format).date()


# ============== Command Handlers ==============

@authorized_only
async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /start command - register user and show welcome message."""
    user = await get_user(update)
    name = update.effective_user.first_name or "there"
    user_id = update.effective_user.id
    
    is_admin = queries.is_user_admin(user_id) or user_id == ADMIN_USER_ID
    
    welcome_message = f"""
👋 *Welcome to Budget Bot, {name}!*

I'll help you track your expenses and manage your budget.

*Quick Start:*
1️⃣ Set a budget with /setbudget
2️⃣ Log expenses by sending: `50 groceries`
3️⃣ I'll ask you to pick a category
4️⃣ Check your status with /budget

*Commands:*
• /setbudget - Set a new budget period
• /budget - View current budget status
• /history - View expense history
• /cancel - Cancel current operation
"""
    
    if is_admin:
        welcome_message += """
*Admin Commands:* 👑
• /adduser <id> - Authorize a new user
• /removeuser <id> - Remove user access
• /listusers - View all authorized users
• /myid - Show your Telegram ID
"""
    
    welcome_message += "\nReady to start tracking? 🚀"
    
    await update.message.reply_text(welcome_message, parse_mode="Markdown")


@authorized_only
async def cancel_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /cancel command - cancel any ongoing operation."""
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END


@authorized_only
async def budget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /budget command - show current budget status."""
    user = await get_user(update)
    status = get_user_budget_status(user["id"])
    
    if not status:
        await update.message.reply_text(
            "📊 You don't have an active budget.\n\n"
            "Use /setbudget to set up a budget period."
        )
        return
    
    message = format_budget_status(status)
    await update.message.reply_text(message, parse_mode="Markdown")


# ============== Set Budget Conversation ==============

@authorized_only
async def setbudget_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle /setbudget command - start budget setting flow."""
    await update.message.reply_text(
        "💰 *Set Your Budget*\n\n"
        "Enter the total budget amount:\n"
        "(e.g., `3000` or `1500.50`)",
        parse_mode="Markdown"
    )
    return ConversationState.WAITING_BUDGET_AMOUNT


async def receive_budget_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive budget amount and ask for start date."""
    text = update.message.text.strip()
    
    try:
        amount = float(text.replace(",", ""))
        if amount <= 0:
            raise ValueError("Amount must be positive")
        if amount > 100_000_000:
            raise ValueError("Amount too large")
    except ValueError as e:
        await update.message.reply_text(
            f"❌ Invalid amount. Please enter a valid number.\n"
            f"Example: `3000` or `1500.50`",
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_BUDGET_AMOUNT
    
    context.user_data["budget_amount"] = amount
    
    # Suggest current date as default
    today = date.today()
    await update.message.reply_text(
        f"✅ Budget amount: ${amount:,.2f}\n\n"
        f"Enter start date (DD-MM-YYYY):\n"
        f"(e.g., `{today.strftime('%d-%m-%Y')}` for today)",
        parse_mode="Markdown"
    )
    return ConversationState.WAITING_START_DATE


async def receive_start_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive start date and ask for end date."""
    text = update.message.text.strip()
    
    try:
        start_date = parse_date(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format. Please use DD-MM-YYYY.\n"
            "Example: `01-01-2025`",
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_START_DATE
    
    context.user_data["start_date"] = start_date
    
    # Suggest end of month as default
    if start_date.month == 12:
        end_suggestion = date(start_date.year + 1, 1, 31)
    else:
        import calendar
        last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        end_suggestion = date(start_date.year, start_date.month, last_day)
    
    await update.message.reply_text(
        f"✅ Start date: {start_date.strftime('%B %d, %Y')}\n\n"
        f"Enter end date (DD-MM-YYYY):\n"
        f"(e.g., `{end_suggestion.strftime('%d-%m-%Y')}` for end of month)",
        parse_mode="Markdown"
    )
    return ConversationState.WAITING_END_DATE


async def receive_end_date(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Receive end date and create the budget."""
    text = update.message.text.strip()
    
    try:
        end_date = parse_date(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid date format. Please use DD-MM-YYYY.\n"
            "Example: `31-01-2025`",
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_END_DATE
    
    start_date = context.user_data.get("start_date")
    if end_date < start_date:
        await update.message.reply_text(
            "❌ End date must be after start date.\n"
            "Please enter a valid end date:",
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_END_DATE
    
    # Create the budget
    user = await get_user(update)
    amount = context.user_data["budget_amount"]
    
    budget = create_user_budget(user["id"], amount, start_date, end_date)
    
    # Calculate daily budget
    days = (end_date - start_date).days + 1
    daily = amount / days
    
    await update.message.reply_text(
        f"✅ *Budget Created!*\n\n"
        f"💰 Total: ${amount:,.2f}\n"
        f"📅 Period: {start_date.strftime('%b %d')} - {end_date.strftime('%b %d, %Y')}\n"
        f"⏳ Duration: {days} days\n"
        f"📊 Daily Budget: ${daily:,.2f}\n\n"
        f"Start logging expenses by sending messages like:\n"
        f"`50 groceries`",
        parse_mode="Markdown"
    )
    
    context.user_data.clear()
    return ConversationHandler.END


# ============== Expense Flow ==============

@authorized_only
async def handle_expense_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle expense message and show category selection."""
    text = update.message.text
    
    # Check if it looks like an expense
    if not is_expense_message(text):
        return ConversationHandler.END
    
    try:
        parsed = parse_expense(text)
    except ExpenseParseError as e:
        await update.message.reply_text(f"❌ {str(e)}")
        return ConversationHandler.END
    
    # Store parsed expense in user data
    context.user_data["pending_expense"] = {
        "amount": parsed.amount,
        "description": parsed.description
    }
    
    # Get categories and show keyboard
    categories = queries.get_all_categories()
    keyboard = build_category_keyboard(categories)
    
    await update.message.reply_text(
        f"💰 *${parsed.amount:,.2f}* - {parsed.description}\n\n"
        f"Select a category:",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    
    return ConversationState.WAITING_CATEGORY


async def handle_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection callback."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_expense":
        context.user_data.clear()
        await query.edit_message_text("❌ Expense cancelled.")
        return ConversationHandler.END
    
    if not data.startswith("category_"):
        return ConversationState.WAITING_CATEGORY
    
    category_id = data.replace("category_", "")
    pending = context.user_data.get("pending_expense")
    
    if not pending:
        await query.edit_message_text("❌ Session expired. Please try again.")
        return ConversationHandler.END
    
    # Get category info
    category = queries.get_category_by_id(category_id)
    if not category:
        await query.edit_message_text("❌ Invalid category. Please try again.")
        return ConversationHandler.END
    
    # Get user and active budget
    user = get_or_create_user_from_telegram(update.effective_user)
    today = date.today()
    budget = queries.get_active_budget(user["id"], today)
    
    # Create the expense
    expense = queries.create_expense(
        user_id=user["id"],
        category_id=category_id,
        amount=pending["amount"],
        description=pending["description"],
        expense_date=today,
        budget_id=budget["id"] if budget else None
    )
    
    # Get updated budget status
    status = get_user_budget_status(user["id"])
    
    if status:
        message = format_expense_confirmation(
            amount=pending["amount"],
            description=pending["description"],
            category_name=category["name"],
            category_emoji=category["emoji"],
            daily_budget=status.daily_budget,
            remaining_budget=status.remaining_budget
        )
    else:
        message = (
            f"✅ *Expense Added!*\n\n"
            f"💰 ${pending['amount']:,.2f} - {pending['description']}\n"
            f"🏷️ Category: {category['emoji']} {category['name']}\n\n"
            f"💡 Set a budget with /setbudget to track daily spending!"
        )
    
    await query.edit_message_text(message, parse_mode="Markdown")
    context.user_data.clear()
    return ConversationHandler.END


# ============== History & Management ==============

EXPENSES_PER_PAGE = 5


@authorized_only
async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /history command - show expense history."""
    await show_history_page(update, context, page=0)


async def show_history_page(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    page: int = 0,
    edit_message: bool = False
) -> None:
    """Show a page of expense history."""
    user = await get_user(update)
    
    # Get total count and expenses
    total_count = queries.get_user_expense_count(user["id"])
    
    if total_count == 0:
        message = "📋 *Expense History*\n\nNo expenses recorded yet."
        if edit_message and update.callback_query:
            await update.callback_query.edit_message_text(message, parse_mode="Markdown")
        else:
            await update.message.reply_text(message, parse_mode="Markdown")
        return
    
    # Calculate pagination
    total_pages = (total_count + EXPENSES_PER_PAGE - 1) // EXPENSES_PER_PAGE
    offset = page * EXPENSES_PER_PAGE
    
    expenses = queries.get_user_expenses(user["id"], limit=EXPENSES_PER_PAGE, offset=offset)
    
    # Build message
    lines = ["📋 *Expense History*\n"]
    
    for expense in expenses:
        exp_date = datetime.fromisoformat(expense["expense_date"]).strftime("%b %d")
        cat = expense.get("categories", {})
        emoji = cat.get("emoji", "📦")
        cat_name = cat.get("name", "Unknown")
        
        lines.append(
            f"\n{emoji} *${float(expense['amount']):,.2f}* - {expense['description']}\n"
            f"    {exp_date} • {cat_name}"
        )
    
    lines.append(f"\n\n📊 Total: {total_count} expenses")
    
    message = "".join(lines)
    
    # Build inline keyboard for each expense
    buttons = []
    for expense in expenses:
        buttons.append([
            InlineKeyboardButton(
                f"✏️ Edit ${float(expense['amount']):,.2f}",
                callback_data=f"edit_{expense['id']}"
            ),
            InlineKeyboardButton(
                "🗑️",
                callback_data=f"delete_{expense['id']}"
            )
        ])
    
    # Add navigation
    nav_row = []
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"history_page_{page - 1}"))
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"history_page_{page + 1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    keyboard = InlineKeyboardMarkup(buttons) if buttons else None
    
    if edit_message and update.callback_query:
        await update.callback_query.edit_message_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            message, reply_markup=keyboard, parse_mode="Markdown"
        )


async def handle_history_navigation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle history page navigation."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    if data == "noop":
        return
    
    if data.startswith("history_page_"):
        page = int(data.replace("history_page_", ""))
        await show_history_page(update, context, page=page, edit_message=True)


# ============== Edit Expense ==============

async def handle_edit_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit expense button."""
    query = update.callback_query
    await query.answer()
    
    expense_id = query.data.replace("edit_", "")
    expense = queries.get_expense_by_id(expense_id)
    
    if not expense:
        await query.edit_message_text("❌ Expense not found.")
        return ConversationHandler.END
    
    context.user_data["editing_expense_id"] = expense_id
    
    cat = expense.get("categories", {})
    emoji = cat.get("emoji", "📦")
    cat_name = cat.get("name", "Unknown")
    
    keyboard = build_edit_options_keyboard(expense_id)
    
    await query.edit_message_text(
        f"✏️ *Edit Expense*\n\n"
        f"💰 Amount: ${float(expense['amount']):,.2f}\n"
        f"📝 Description: {expense['description']}\n"
        f"🏷️ Category: {emoji} {cat_name}\n\n"
        f"What would you like to change?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationState.WAITING_EDIT_CHOICE


async def handle_edit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle edit choice selection."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_edit":
        context.user_data.clear()
        await query.edit_message_text("❌ Edit cancelled.")
        return ConversationHandler.END
    
    if data.startswith("edit_amount_"):
        expense_id = data.replace("edit_amount_", "")
        context.user_data["editing_expense_id"] = expense_id
        await query.edit_message_text(
            "💰 Enter the new amount:\n"
            "(e.g., `50` or `25.50`)",
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_NEW_AMOUNT
    
    elif data.startswith("edit_desc_"):
        expense_id = data.replace("edit_desc_", "")
        context.user_data["editing_expense_id"] = expense_id
        await query.edit_message_text(
            "📝 Enter the new description:",
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_NEW_DESCRIPTION
    
    elif data.startswith("edit_cat_"):
        expense_id = data.replace("edit_cat_", "")
        context.user_data["editing_expense_id"] = expense_id
        context.user_data["editing_category"] = True
        
        categories = queries.get_all_categories()
        keyboard = build_category_keyboard(categories)
        
        await query.edit_message_text(
            "🏷️ Select the new category:",
            reply_markup=keyboard,
            parse_mode="Markdown"
        )
        return ConversationState.WAITING_CATEGORY
    
    return ConversationHandler.END


async def handle_new_amount(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new amount input."""
    text = update.message.text.strip()
    expense_id = context.user_data.get("editing_expense_id")
    
    try:
        amount = float(text.replace(",", ""))
        if amount <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_text(
            "❌ Invalid amount. Please enter a positive number:"
        )
        return ConversationState.WAITING_NEW_AMOUNT
    
    queries.update_expense(expense_id, amount=amount)
    
    await update.message.reply_text(
        f"✅ Amount updated to ${amount:,.2f}",
        parse_mode="Markdown"
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def handle_new_description(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle new description input."""
    description = update.message.text.strip()
    expense_id = context.user_data.get("editing_expense_id")
    
    if not description or len(description) > 200:
        await update.message.reply_text(
            "❌ Description must be 1-200 characters. Try again:"
        )
        return ConversationState.WAITING_NEW_DESCRIPTION
    
    queries.update_expense(expense_id, description=description)
    
    await update.message.reply_text(
        f"✅ Description updated to: {description}",
        parse_mode="Markdown"
    )
    
    context.user_data.clear()
    return ConversationHandler.END


async def handle_edit_category_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle category selection for editing."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_expense":
        context.user_data.clear()
        await query.edit_message_text("❌ Edit cancelled.")
        return ConversationHandler.END
    
    # Check if this is an edit operation
    if not context.user_data.get("editing_category"):
        # This is a new expense, delegate to the regular handler
        return await handle_category_selection(update, context)
    
    if not data.startswith("category_"):
        return ConversationState.WAITING_CATEGORY
    
    category_id = data.replace("category_", "")
    expense_id = context.user_data.get("editing_expense_id")
    
    category = queries.get_category_by_id(category_id)
    if not category:
        await query.edit_message_text("❌ Invalid category.")
        return ConversationHandler.END
    
    queries.update_expense(expense_id, category_id=category_id)
    
    await query.edit_message_text(
        f"✅ Category updated to {category['emoji']} {category['name']}",
        parse_mode="Markdown"
    )
    
    context.user_data.clear()
    return ConversationHandler.END


# ============== Delete Expense ==============

async def handle_delete_expense(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle delete expense button."""
    query = update.callback_query
    await query.answer()
    
    expense_id = query.data.replace("delete_", "")
    expense = queries.get_expense_by_id(expense_id)
    
    if not expense:
        await query.edit_message_text("❌ Expense not found.")
        return ConversationHandler.END
    
    keyboard = build_delete_confirmation_keyboard(expense_id)
    
    await query.edit_message_text(
        f"🗑️ *Delete Expense?*\n\n"
        f"💰 ${float(expense['amount']):,.2f} - {expense['description']}\n\n"
        f"Are you sure you want to delete this expense?",
        reply_markup=keyboard,
        parse_mode="Markdown"
    )
    return ConversationState.WAITING_DELETE_CONFIRM


async def handle_delete_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle delete confirmation."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    if data == "cancel_delete":
        await query.edit_message_text("❌ Delete cancelled.")
        return ConversationHandler.END
    
    if data.startswith("confirm_delete_"):
        expense_id = data.replace("confirm_delete_", "")
        queries.delete_expense(expense_id)
        
        # Get updated budget status
        user = get_or_create_user_from_telegram(update.effective_user)
        status = get_user_budget_status(user["id"])
        
        message = "✅ Expense deleted!"
        if status:
            message += f"\n\n📊 Updated Daily Budget: ${status.daily_budget:,.2f}"
        
        await query.edit_message_text(message, parse_mode="Markdown")
    
    return ConversationHandler.END


# ============== Admin Commands ==============

@admin_only
async def adduser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /adduser command - add a new authorized user."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/adduser <telegram_user_id>`\n\n"
            "Example: `/adduser 123456789`\n\n"
            "To find someone's Telegram ID, ask them to message @userinfobot",
            parse_mode="Markdown"
        )
        return
    
    try:
        new_user_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
        return
    
    # Check if already authorized
    if queries.is_user_authorized(new_user_id):
        await update.message.reply_text(f"⚠️ User `{new_user_id}` is already authorized.", parse_mode="Markdown")
        return
    
    # Add the user
    queries.add_authorized_user(
        telegram_user_id=new_user_id,
        username=None,  # Will be updated when they first use the bot
        first_name=None,
        is_admin=False,
        added_by_telegram_id=update.effective_user.id
    )
    
    await update.message.reply_text(
        f"✅ User `{new_user_id}` has been authorized!\n\n"
        f"They can now use the bot.",
        parse_mode="Markdown"
    )


@admin_only
async def removeuser_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /removeuser command - remove an authorized user."""
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Usage: `/removeuser <telegram_user_id>`\n\n"
            "Example: `/removeuser 123456789`",
            parse_mode="Markdown"
        )
        return
    
    try:
        user_id_to_remove = int(context.args[0])
    except ValueError:
        await update.message.reply_text("❌ Invalid user ID. Must be a number.")
        return
    
    # Prevent removing yourself
    if user_id_to_remove == update.effective_user.id:
        await update.message.reply_text("❌ You cannot remove yourself!")
        return
    
    # Prevent removing the main admin
    if user_id_to_remove == ADMIN_USER_ID:
        await update.message.reply_text("❌ Cannot remove the main admin!")
        return
    
    # Check if user exists
    if not queries.is_user_authorized(user_id_to_remove):
        await update.message.reply_text(f"⚠️ User `{user_id_to_remove}` is not authorized.", parse_mode="Markdown")
        return
    
    # Remove the user
    queries.remove_authorized_user(user_id_to_remove)
    
    await update.message.reply_text(
        f"✅ User `{user_id_to_remove}` has been removed.\n\n"
        f"They can no longer use the bot.",
        parse_mode="Markdown"
    )


@admin_only
async def listusers_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /listusers command - list all authorized users."""
    users = queries.get_all_authorized_users()
    
    if not users:
        await update.message.reply_text("No authorized users found.")
        return
    
    lines = ["👥 *Authorized Users*\n"]
    
    for user in users:
        user_id = user["telegram_user_id"]
        username = user.get("username")
        first_name = user.get("first_name")
        is_admin = user.get("is_admin", False)
        
        user_display = f"`{user_id}`"
        if first_name:
            user_display += f" - {first_name}"
        if username:
            user_display += f" (@{username})"
        if is_admin:
            user_display += " 👑"
        
        lines.append(f"• {user_display}")
    
    lines.append(f"\n📊 Total: {len(users)} users")
    
    await update.message.reply_text("\n".join(lines), parse_mode="Markdown")


@admin_only
async def myid_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle /myid command - show user's Telegram ID."""
    user_id = update.effective_user.id
    username = update.effective_user.username
    first_name = update.effective_user.first_name
    
    message = f"🆔 *Your Telegram Info*\n\n"
    message += f"User ID: `{user_id}`\n"
    if first_name:
        message += f"Name: {first_name}\n"
    if username:
        message += f"Username: @{username}\n"
    
    if queries.is_user_admin(user_id) or user_id == ADMIN_USER_ID:
        message += f"\n👑 You are an admin"
    
    await update.message.reply_text(message, parse_mode="Markdown")


# ============== Fallback Handler ==============

async def handle_unknown_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle unknown messages."""
    await update.message.reply_text(
        "🤔 I didn't understand that.\n\n"
        "To log an expense, send: `50 groceries`\n"
        "For help, send /start",
        parse_mode="Markdown"
    )


# ============== Build Conversation Handlers ==============

def build_expense_conversation_handler() -> ConversationHandler:
    """Build the expense adding conversation handler."""
    return ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.TEXT & ~filters.COMMAND & filters.Regex(r'^\d'),
                handle_expense_message
            )
        ],
        states={
            ConversationState.WAITING_CATEGORY: [
                CallbackQueryHandler(handle_category_selection)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        allow_reentry=True,
        per_message=False
    )


def build_budget_conversation_handler() -> ConversationHandler:
    """Build the budget setting conversation handler."""
    return ConversationHandler(
        entry_points=[
            CommandHandler("setbudget", setbudget_command)
        ],
        states={
            ConversationState.WAITING_BUDGET_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_budget_amount)
            ],
            ConversationState.WAITING_START_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_start_date)
            ],
            ConversationState.WAITING_END_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_end_date)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        allow_reentry=True
    )


def build_edit_conversation_handler() -> ConversationHandler:
    """Build the expense editing conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_edit_expense, pattern=r'^edit_[a-f0-9-]+$')
        ],
        states={
            ConversationState.WAITING_EDIT_CHOICE: [
                CallbackQueryHandler(handle_edit_choice)
            ],
            ConversationState.WAITING_NEW_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_amount)
            ],
            ConversationState.WAITING_NEW_DESCRIPTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_description)
            ],
            ConversationState.WAITING_CATEGORY: [
                CallbackQueryHandler(handle_edit_category_selection)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        allow_reentry=True
    )


def build_delete_conversation_handler() -> ConversationHandler:
    """Build the expense deletion conversation handler."""
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(handle_delete_expense, pattern=r'^delete_[a-f0-9-]+$')
        ],
        states={
            ConversationState.WAITING_DELETE_CONFIRM: [
                CallbackQueryHandler(handle_delete_confirmation)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel_command)
        ],
        allow_reentry=True
    )

