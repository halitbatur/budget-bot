"""Budget calculation logic."""
from dataclasses import dataclass
from datetime import date
from typing import Optional


@dataclass
class BudgetStatus:
    """Represents the current budget status."""
    total_budget: float
    total_spent: float
    remaining_budget: float
    start_date: date
    end_date: date
    days_total: int
    days_passed: int
    days_remaining: int
    daily_budget: float
    
    @property
    def spent_percentage(self) -> float:
        """Percentage of budget spent."""
        if self.total_budget <= 0:
            return 0.0
        return (self.total_spent / self.total_budget) * 100
    
    @property
    def is_over_budget(self) -> bool:
        """Check if spending is over budget."""
        return self.remaining_budget < 0
    
    @property
    def daily_average_spent(self) -> float:
        """Average daily spending so far."""
        if self.days_passed <= 0:
            return 0.0
        return self.total_spent / self.days_passed


def calculate_budget_status(
    total_budget: float,
    total_spent: float,
    start_date: date,
    end_date: date,
    current_date: Optional[date] = None
) -> BudgetStatus:
    """Calculate the current budget status.
    
    Args:
        total_budget: Total budget amount for the period.
        total_spent: Total amount spent so far.
        start_date: Budget period start date.
        end_date: Budget period end date.
        current_date: Current date (defaults to today).
    
    Returns:
        BudgetStatus with all calculated values.
    """
    if current_date is None:
        current_date = date.today()
    
    # Calculate days
    days_total = (end_date - start_date).days + 1
    
    # Days passed is from start_date to current_date (inclusive)
    if current_date < start_date:
        days_passed = 0
    elif current_date > end_date:
        days_passed = days_total
    else:
        days_passed = (current_date - start_date).days + 1
    
    # Days remaining (including today if within range)
    if current_date > end_date:
        days_remaining = 0
    elif current_date < start_date:
        days_remaining = days_total
    else:
        days_remaining = (end_date - current_date).days + 1
    
    # Calculate remaining budget
    remaining_budget = total_budget - total_spent
    
    # Calculate daily budget based on remaining days
    if days_remaining > 0:
        daily_budget = remaining_budget / days_remaining
    else:
        daily_budget = 0.0
    
    return BudgetStatus(
        total_budget=total_budget,
        total_spent=total_spent,
        remaining_budget=remaining_budget,
        start_date=start_date,
        end_date=end_date,
        days_total=days_total,
        days_passed=days_passed,
        days_remaining=days_remaining,
        daily_budget=daily_budget
    )


def format_budget_status(status: BudgetStatus) -> str:
    """Format budget status as a user-friendly message.
    
    Args:
        status: The BudgetStatus to format.
    
    Returns:
        Formatted string with budget information.
    """
    lines = [
        "📊 *Budget Status*",
        "",
        f"💰 Total Budget: ${status.total_budget:,.2f}",
        f"💸 Total Spent: ${status.total_spent:,.2f} ({status.spent_percentage:.1f}%)",
        f"💵 Remaining: ${status.remaining_budget:,.2f}",
        "",
        f"📅 Period: {status.start_date.strftime('%b %d')} - {status.end_date.strftime('%b %d, %Y')}",
        f"⏳ Days: {status.days_passed}/{status.days_total} ({status.days_remaining} remaining)",
        "",
    ]
    
    if status.is_over_budget:
        lines.append(f"🚨 *OVER BUDGET by ${abs(status.remaining_budget):,.2f}!*")
    else:
        lines.append(f"✅ *Daily Budget: ${status.daily_budget:,.2f}*")
    
    if status.days_passed > 0:
        lines.append(f"📈 Daily Average: ${status.daily_average_spent:,.2f}")
    
    return "\n".join(lines)


def format_expense_confirmation(
    amount: float,
    description: str,
    category_name: str,
    category_emoji: str,
    daily_budget: float,
    remaining_budget: float
) -> str:
    """Format expense confirmation message.
    
    Args:
        amount: Expense amount.
        description: Expense description.
        category_name: Category name.
        category_emoji: Category emoji.
        daily_budget: Updated daily budget.
        remaining_budget: Total remaining budget.
    
    Returns:
        Formatted confirmation message.
    """
    lines = [
        "✅ *Expense Added!*",
        "",
        f"💰 ${amount:,.2f} - {description}",
        f"🏷️ Category: {category_emoji} {category_name}",
        "",
    ]
    
    if daily_budget < 0:
        lines.append(f"🚨 Over budget! Remaining: ${remaining_budget:,.2f}")
    else:
        lines.append(f"📊 Daily Budget: ${daily_budget:,.2f}")
        lines.append(f"💵 Total Remaining: ${remaining_budget:,.2f}")
    
    return "\n".join(lines)

