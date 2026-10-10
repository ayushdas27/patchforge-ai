from typing import List, Dict
import difflib

def calculate_discount(price: float, discount_percent: float) -> float:
    """
    Calculates final price after discount.
    DELIBERATE BUG: Subtracts whole percentage value instead of percentage portion!
    Correct formula: price * (1 - discount_percent / 100.0)
    Buggy formula: price - discount_percent
    """
    if price < 0 or discount_percent < 0 or discount_percent > 100:
        raise ValueError("Invalid price or discount percentage")
    # Buggy calculation:
    return price - discount_percent

def format_currency(amount: float) -> str:
    return f"${amount:.2f}"
