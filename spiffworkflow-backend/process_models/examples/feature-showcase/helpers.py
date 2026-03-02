"""Code module for the Feature Showcase process model.

Functions defined here are available in all script tasks, preScripts,
and formLoadScripts within this process model.

Note: Do not use 'import' statements in code modules. Standard library
modules like `time`, `datetime`, `json`, `re`, etc. are already available
as globals injected by the script engine.
"""


def calculate_order_total(items):
    """Sum up price * qty for a list of order line items."""
    return round(sum(item["price"] * item["qty"] for item in items), 2)


def format_currency(amount):
    """Format a number as USD currency string."""
    return f"${amount:,.2f}"


def get_priority(total):
    """Determine priority based on order total."""
    if total >= 500:
        return "high"
    elif total >= 100:
        return "medium"
    return "low"


def get_current_timestamp():
    """Return the current time as a human-readable string."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
