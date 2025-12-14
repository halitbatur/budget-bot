"""Inline keyboard builders for the Telegram bot."""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def build_category_keyboard(categories: list) -> InlineKeyboardMarkup:
    """Build an inline keyboard with category buttons.
    
    Args:
        categories: List of category dictionaries with 'id', 'name', 'emoji' keys.
    
    Returns:
        InlineKeyboardMarkup with category buttons arranged in 2 columns.
    """
    buttons = []
    row = []
    
    for i, category in enumerate(categories):
        button = InlineKeyboardButton(
            text=f"{category['emoji']} {category['name']}",
            callback_data=f"category_{category['id']}"
        )
        row.append(button)
        
        # Create rows of 2 buttons
        if len(row) == 2:
            buttons.append(row)
            row = []
    
    # Add remaining button if odd number
    if row:
        buttons.append(row)
    
    # Add cancel button
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="cancel_expense")])
    
    return InlineKeyboardMarkup(buttons)


def build_expense_actions_keyboard(expense_id: str) -> InlineKeyboardMarkup:
    """Build an inline keyboard for expense actions (edit/delete).
    
    Args:
        expense_id: The UUID of the expense.
    
    Returns:
        InlineKeyboardMarkup with edit and delete buttons.
    """
    buttons = [
        [
            InlineKeyboardButton("✏️ Edit", callback_data=f"edit_{expense_id}"),
            InlineKeyboardButton("🗑️ Delete", callback_data=f"delete_{expense_id}")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def build_edit_options_keyboard(expense_id: str) -> InlineKeyboardMarkup:
    """Build an inline keyboard for edit options.
    
    Args:
        expense_id: The UUID of the expense.
    
    Returns:
        InlineKeyboardMarkup with options to edit amount, description, or cancel.
    """
    buttons = [
        [InlineKeyboardButton("💰 Change Amount", callback_data=f"edit_amount_{expense_id}")],
        [InlineKeyboardButton("📝 Change Description", callback_data=f"edit_desc_{expense_id}")],
        [InlineKeyboardButton("🏷️ Change Category", callback_data=f"edit_cat_{expense_id}")],
        [InlineKeyboardButton("❌ Cancel", callback_data="cancel_edit")]
    ]
    return InlineKeyboardMarkup(buttons)


def build_delete_confirmation_keyboard(expense_id: str) -> InlineKeyboardMarkup:
    """Build a confirmation keyboard for delete action.
    
    Args:
        expense_id: The UUID of the expense.
    
    Returns:
        InlineKeyboardMarkup with confirm and cancel buttons.
    """
    buttons = [
        [
            InlineKeyboardButton("✅ Yes, delete", callback_data=f"confirm_delete_{expense_id}"),
            InlineKeyboardButton("❌ No, keep", callback_data="cancel_delete")
        ]
    ]
    return InlineKeyboardMarkup(buttons)


def build_history_navigation_keyboard(page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Build navigation keyboard for expense history.
    
    Args:
        page: Current page number (0-indexed).
        total_pages: Total number of pages.
    
    Returns:
        InlineKeyboardMarkup with previous/next buttons.
    """
    buttons = []
    nav_row = []
    
    if page > 0:
        nav_row.append(InlineKeyboardButton("⬅️ Previous", callback_data=f"history_page_{page - 1}"))
    
    nav_row.append(InlineKeyboardButton(f"{page + 1}/{total_pages}", callback_data="noop"))
    
    if page < total_pages - 1:
        nav_row.append(InlineKeyboardButton("➡️ Next", callback_data=f"history_page_{page + 1}"))
    
    if nav_row:
        buttons.append(nav_row)
    
    return InlineKeyboardMarkup(buttons) if buttons else None

