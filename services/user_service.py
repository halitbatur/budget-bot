"""User management service."""
from datetime import date
from typing import Optional
from telegram import User as TelegramUser

from database import queries
from services.budget_calculator import BudgetStatus, calculate_budget_status


def get_or_create_user_from_telegram(telegram_user: TelegramUser) -> dict:
    """Get or create a user from Telegram user info.
    
    Args:
        telegram_user: The Telegram User object.
    
    Returns:
        The user dict from the database.
    """
    return queries.get_or_create_user(
        telegram_user_id=telegram_user.id,
        username=telegram_user.username,
        first_name=telegram_user.first_name
    )


def get_user_budget_status(user_id: str, current_date: Optional[date] = None) -> Optional[BudgetStatus]:
    """Get the current budget status for a user.
    
    Args:
        user_id: The user's UUID.
        current_date: Optional date to calculate status for (defaults to today).
    
    Returns:
        BudgetStatus or None if no active budget.
    """
    if current_date is None:
        current_date = date.today()
    
    budget = queries.get_active_budget(user_id, current_date)
    if not budget:
        return None
    
    # Parse dates from budget
    start_date = date.fromisoformat(budget["start_date"])
    end_date = date.fromisoformat(budget["end_date"])
    
    # Get total spent in the budget period
    total_spent = queries.get_total_spent_in_range(user_id, start_date, end_date)
    
    return calculate_budget_status(
        total_budget=float(budget["total_amount"]),
        total_spent=total_spent,
        start_date=start_date,
        end_date=end_date,
        current_date=current_date
    )


def create_user_budget(
    user_id: str,
    total_amount: float,
    start_date: date,
    end_date: date
) -> dict:
    """Create a new budget for a user.
    
    Args:
        user_id: The user's UUID.
        total_amount: Total budget amount.
        start_date: Budget period start date.
        end_date: Budget period end date.
    
    Returns:
        The created budget dict.
    """
    return queries.create_budget(user_id, total_amount, start_date, end_date)

