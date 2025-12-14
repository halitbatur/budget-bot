"""Database query functions for the budget bot."""
from datetime import date
from typing import Optional
from database.supabase_client import get_supabase_client


# ============== Authorization Queries ==============

def is_user_authorized(telegram_user_id: int) -> bool:
    """Check if a user is authorized to use the bot.
    
    Args:
        telegram_user_id: The Telegram user ID.
    
    Returns:
        True if authorized, False otherwise.
    """
    client = get_supabase_client()
    response = client.table("authorized_users").select("id").eq("telegram_user_id", telegram_user_id).execute()
    return len(response.data) > 0


def is_user_admin(telegram_user_id: int) -> bool:
    """Check if a user is an admin.
    
    Args:
        telegram_user_id: The Telegram user ID.
    
    Returns:
        True if admin, False otherwise.
    """
    client = get_supabase_client()
    response = client.table("authorized_users").select("is_admin").eq("telegram_user_id", telegram_user_id).execute()
    return response.data and response.data[0].get("is_admin", False)


def add_authorized_user(
    telegram_user_id: int,
    username: Optional[str],
    first_name: Optional[str],
    is_admin: bool = False,
    added_by_telegram_id: Optional[int] = None
) -> dict:
    """Add a new authorized user.
    
    Args:
        telegram_user_id: The Telegram user ID.
        username: The Telegram username (optional).
        first_name: The user's first name (optional).
        is_admin: Whether the user is an admin.
        added_by_telegram_id: The admin who added this user.
    
    Returns:
        The created authorized_user dict.
    """
    client = get_supabase_client()
    response = client.table("authorized_users").insert({
        "telegram_user_id": telegram_user_id,
        "username": username,
        "first_name": first_name,
        "is_admin": is_admin,
        "added_by_telegram_id": added_by_telegram_id
    }).execute()
    return response.data[0]


def remove_authorized_user(telegram_user_id: int) -> bool:
    """Remove an authorized user.
    
    Args:
        telegram_user_id: The Telegram user ID.
    
    Returns:
        True if removed successfully.
    """
    client = get_supabase_client()
    client.table("authorized_users").delete().eq("telegram_user_id", telegram_user_id).execute()
    return True


def get_all_authorized_users() -> list[dict]:
    """Get all authorized users.
    
    Returns:
        List of authorized user dicts.
    """
    client = get_supabase_client()
    response = client.table("authorized_users").select("*").order("created_at", desc=True).execute()
    return response.data


def get_authorized_user(telegram_user_id: int) -> Optional[dict]:
    """Get an authorized user by Telegram ID.
    
    Args:
        telegram_user_id: The Telegram user ID.
    
    Returns:
        Authorized user dict or None if not found.
    """
    client = get_supabase_client()
    response = client.table("authorized_users").select("*").eq("telegram_user_id", telegram_user_id).execute()
    return response.data[0] if response.data else None


# ============== User Queries ==============

def get_user_by_telegram_id(telegram_user_id: int) -> Optional[dict]:
    """Get a user by their Telegram user ID.
    
    Args:
        telegram_user_id: The Telegram user ID.
    
    Returns:
        User dict or None if not found.
    """
    client = get_supabase_client()
    response = client.table("users").select("*").eq("telegram_user_id", telegram_user_id).execute()
    return response.data[0] if response.data else None


def create_user(telegram_user_id: int, username: Optional[str], first_name: Optional[str]) -> dict:
    """Create a new user.
    
    Args:
        telegram_user_id: The Telegram user ID.
        username: The Telegram username (optional).
        first_name: The user's first name (optional).
    
    Returns:
        The created user dict.
    """
    client = get_supabase_client()
    response = client.table("users").insert({
        "telegram_user_id": telegram_user_id,
        "username": username,
        "first_name": first_name
    }).execute()
    return response.data[0]


def get_or_create_user(telegram_user_id: int, username: Optional[str], first_name: Optional[str]) -> dict:
    """Get an existing user or create a new one.
    
    Args:
        telegram_user_id: The Telegram user ID.
        username: The Telegram username (optional).
        first_name: The user's first name (optional).
    
    Returns:
        The user dict.
    """
    user = get_user_by_telegram_id(telegram_user_id)
    if user:
        return user
    return create_user(telegram_user_id, username, first_name)


# ============== Category Queries ==============

def get_all_categories() -> list[dict]:
    """Get all expense categories.
    
    Returns:
        List of category dicts with 'id', 'name', 'emoji' keys.
    """
    client = get_supabase_client()
    response = client.table("categories").select("*").order("name").execute()
    return response.data


def get_category_by_id(category_id: str) -> Optional[dict]:
    """Get a category by its ID.
    
    Args:
        category_id: The category UUID.
    
    Returns:
        Category dict or None if not found.
    """
    client = get_supabase_client()
    response = client.table("categories").select("*").eq("id", category_id).execute()
    return response.data[0] if response.data else None


# ============== Budget Queries ==============

def get_active_budget(user_id: str, current_date: date) -> Optional[dict]:
    """Get the active budget for a user on a given date.
    
    Args:
        user_id: The user's UUID.
        current_date: The date to check.
    
    Returns:
        Budget dict or None if no active budget.
    """
    client = get_supabase_client()
    date_str = current_date.isoformat()
    response = client.table("budgets").select("*").eq("user_id", user_id).lte("start_date", date_str).gte("end_date", date_str).order("created_at", desc=True).limit(1).execute()
    return response.data[0] if response.data else None


def create_budget(user_id: str, total_amount: float, start_date: date, end_date: date) -> dict:
    """Create a new budget period.
    
    Args:
        user_id: The user's UUID.
        total_amount: The total budget amount.
        start_date: Budget period start date.
        end_date: Budget period end date.
    
    Returns:
        The created budget dict.
    """
    client = get_supabase_client()
    response = client.table("budgets").insert({
        "user_id": user_id,
        "total_amount": total_amount,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat()
    }).execute()
    return response.data[0]


def get_user_budgets(user_id: str, limit: int = 10) -> list[dict]:
    """Get recent budgets for a user.
    
    Args:
        user_id: The user's UUID.
        limit: Maximum number of budgets to return.
    
    Returns:
        List of budget dicts.
    """
    client = get_supabase_client()
    response = client.table("budgets").select("*").eq("user_id", user_id).order("created_at", desc=True).limit(limit).execute()
    return response.data


# ============== Expense Queries ==============

def create_expense(
    user_id: str,
    category_id: str,
    amount: float,
    description: str,
    expense_date: date,
    budget_id: Optional[str] = None
) -> dict:
    """Create a new expense.
    
    Args:
        user_id: The user's UUID.
        category_id: The category UUID.
        amount: The expense amount.
        description: Description of the expense.
        expense_date: Date of the expense.
        budget_id: Optional budget UUID to associate with.
    
    Returns:
        The created expense dict.
    """
    client = get_supabase_client()
    data = {
        "user_id": user_id,
        "category_id": category_id,
        "amount": amount,
        "description": description,
        "expense_date": expense_date.isoformat()
    }
    if budget_id:
        data["budget_id"] = budget_id
    
    response = client.table("expenses").insert(data).execute()
    return response.data[0]


def get_expense_by_id(expense_id: str) -> Optional[dict]:
    """Get an expense by its ID.
    
    Args:
        expense_id: The expense UUID.
    
    Returns:
        Expense dict or None if not found.
    """
    client = get_supabase_client()
    response = client.table("expenses").select("*, categories(name, emoji)").eq("id", expense_id).execute()
    return response.data[0] if response.data else None


def get_expenses_for_budget(user_id: str, start_date: date, end_date: date) -> list[dict]:
    """Get all expenses for a user within a date range.
    
    Args:
        user_id: The user's UUID.
        start_date: Start date of the range.
        end_date: End date of the range.
    
    Returns:
        List of expense dicts with category info.
    """
    client = get_supabase_client()
    response = client.table("expenses").select("*, categories(name, emoji)").eq("user_id", user_id).gte("expense_date", start_date.isoformat()).lte("expense_date", end_date.isoformat()).order("expense_date", desc=True).order("created_at", desc=True).execute()
    return response.data


def get_user_expenses(user_id: str, limit: int = 20, offset: int = 0) -> list[dict]:
    """Get paginated expenses for a user.
    
    Args:
        user_id: The user's UUID.
        limit: Maximum number of expenses per page.
        offset: Number of expenses to skip.
    
    Returns:
        List of expense dicts with category info.
    """
    client = get_supabase_client()
    response = client.table("expenses").select("*, categories(name, emoji)").eq("user_id", user_id).order("expense_date", desc=True).order("created_at", desc=True).range(offset, offset + limit - 1).execute()
    return response.data


def get_user_expense_count(user_id: str) -> int:
    """Get total count of expenses for a user.
    
    Args:
        user_id: The user's UUID.
    
    Returns:
        Total number of expenses.
    """
    client = get_supabase_client()
    response = client.table("expenses").select("id", count="exact").eq("user_id", user_id).execute()
    return response.count or 0


def update_expense(expense_id: str, **kwargs) -> dict:
    """Update an expense.
    
    Args:
        expense_id: The expense UUID.
        **kwargs: Fields to update (amount, description, category_id).
    
    Returns:
        The updated expense dict.
    """
    client = get_supabase_client()
    response = client.table("expenses").update(kwargs).eq("id", expense_id).execute()
    return response.data[0] if response.data else None


def delete_expense(expense_id: str) -> bool:
    """Delete an expense.
    
    Args:
        expense_id: The expense UUID.
    
    Returns:
        True if deleted successfully.
    """
    client = get_supabase_client()
    client.table("expenses").delete().eq("id", expense_id).execute()
    return True


def get_total_spent_in_range(user_id: str, start_date: date, end_date: date) -> float:
    """Get total amount spent in a date range.
    
    Args:
        user_id: The user's UUID.
        start_date: Start date of the range.
        end_date: End date of the range.
    
    Returns:
        Total amount spent.
    """
    expenses = get_expenses_for_budget(user_id, start_date, end_date)
    return sum(float(e["amount"]) for e in expenses)

