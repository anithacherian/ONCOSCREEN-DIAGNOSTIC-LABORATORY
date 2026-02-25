# your_app/templatetags/currency_filters.py
from django import template
from babel.numbers import format_currency
from decimal import Decimal, InvalidOperation

register = template.Library()

@register.filter
def inr_format(value):
    try:
        if value is None:
            return "₹ 0.00"

        # Ensure value is Decimal safely
        if not isinstance(value, Decimal):
            value = Decimal(str(value))

        return format_currency(value, "INR", locale="en_IN")

    except (InvalidOperation, TypeError, ValueError):
        return "₹ 0.00"