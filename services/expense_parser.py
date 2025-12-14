"""Parse expense messages in the format '50 groceries'."""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class ParsedExpense:
    """Represents a parsed expense from user input."""
    amount: float
    description: str


class ExpenseParseError(Exception):
    """Raised when expense parsing fails."""
    pass


def parse_expense(message: str) -> ParsedExpense:
    """Parse an expense message in the format '<amount> <description>'.
    
    Args:
        message: The user's message, e.g. '50 groceries' or '12.50 coffee'
    
    Returns:
        ParsedExpense with amount and description.
    
    Raises:
        ExpenseParseError: If the message format is invalid.
    
    Examples:
        >>> parse_expense("50 groceries")
        ParsedExpense(amount=50.0, description='groceries')
        >>> parse_expense("12.50 coffee with friends")
        ParsedExpense(amount=12.5, description='coffee with friends')
    """
    message = message.strip()
    
    if not message:
        raise ExpenseParseError("Empty message")
    
    # Match amount at the beginning (integer or decimal)
    # Supports: 50, 50.5, 50.50, .50
    pattern = r'^(\d+\.?\d*|\.\d+)\s+(.+)$'
    match = re.match(pattern, message)
    
    if not match:
        raise ExpenseParseError(
            "Invalid format. Please use: <amount> <description>\n"
            "Example: 50 groceries"
        )
    
    amount_str, description = match.groups()
    
    try:
        amount = float(amount_str)
    except ValueError:
        raise ExpenseParseError(f"Invalid amount: {amount_str}")
    
    if amount <= 0:
        raise ExpenseParseError("Amount must be greater than 0")
    
    if amount > 1_000_000:
        raise ExpenseParseError("Amount seems too large. Please check and try again.")
    
    description = description.strip()
    if not description:
        raise ExpenseParseError("Description cannot be empty")
    
    if len(description) > 200:
        raise ExpenseParseError("Description is too long (max 200 characters)")
    
    return ParsedExpense(amount=amount, description=description)


def is_expense_message(message: str) -> bool:
    """Check if a message looks like an expense entry.
    
    This is used to determine if we should try to parse the message as an expense.
    
    Args:
        message: The user's message.
    
    Returns:
        True if the message starts with a number (likely an expense).
    """
    message = message.strip()
    if not message:
        return False
    
    # Check if message starts with a digit or decimal point
    return bool(re.match(r'^[\d.]', message))

