from dataclasses import dataclass


@dataclass(frozen=True)
class LineTotals:
    subtotal_minor: int
    discount_minor: int
    taxable_minor: int
    tax_minor: int
    total_minor: int


def percentage_amount(amount_minor: int, basis_points: int) -> int:
    """Round half-up using integers; financial authority never uses binary floats."""
    return (amount_minor * basis_points + 5000) // 10000


def calculate_line(quantity: int, unit_price_minor: int, discount_type: str,
                   discount_value: int, tax_rate_bps: int) -> LineTotals:
    if quantity <= 0 or unit_price_minor < 0 or not 0 <= tax_rate_bps <= 10000:
        raise ValueError("Invalid line amount")
    subtotal = quantity * unit_price_minor
    if discount_type == "NONE":
        discount = 0
    elif discount_type == "FIXED":
        discount = discount_value
    elif discount_type == "PERCENTAGE" and 0 <= discount_value <= 10000:
        discount = percentage_amount(subtotal, discount_value)
    else:
        raise ValueError("Invalid discount")
    if discount < 0 or discount > subtotal:
        raise ValueError("Discount cannot exceed line subtotal")
    taxable = subtotal - discount
    tax = percentage_amount(taxable, tax_rate_bps)
    return LineTotals(subtotal, discount, taxable, tax, taxable + tax)
