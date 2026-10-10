import pytest
from pricing import calculate_discount, format_currency

def test_format_currency():
    assert format_currency(19.99) == "$19.99"
    assert format_currency(100.0) == "$100.00"

def test_calculate_discount_zero():
    assert calculate_discount(100.0, 0.0) == 100.0

def test_calculate_discount_fifty_percent():
    # 50% discount on $100 should be $50.00
    assert calculate_discount(100.0, 50.0) == 50.0

def test_calculate_discount_twenty_percent():
    # 20% discount on $50 should be $40.00
    # Buggy code returns 50 - 20 = 30, which causes this test to fail!
    assert calculate_discount(50.0, 20.0) == 40.0

def test_calculate_discount_invalid_inputs():
    with pytest.raises(ValueError):
        calculate_discount(-10.0, 10.0)
    with pytest.raises(ValueError):
        calculate_discount(100.0, 150.0)
