"""Conversation states for the Telegram bot."""
from enum import IntEnum, auto


class ConversationState(IntEnum):
    """States for conversation handlers."""
    # Expense flow states
    WAITING_CATEGORY = auto()
    
    # Budget setting flow states
    WAITING_BUDGET_AMOUNT = auto()
    WAITING_START_DATE = auto()
    WAITING_END_DATE = auto()
    
    # Edit flow states
    WAITING_EDIT_CHOICE = auto()
    WAITING_NEW_AMOUNT = auto()
    WAITING_NEW_DESCRIPTION = auto()
    
    # Delete confirmation
    WAITING_DELETE_CONFIRM = auto()

