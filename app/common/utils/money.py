import re
from decimal import Decimal, ROUND_HALF_UP, InvalidOperation
from typing import Annotated, Optional, Union, Any
from pydantic import PlainSerializer, BeforeValidator, WithJsonSchema

# Maximum realistic monetary limit (1 Trillion)
MAX_MONETARY_LIMIT = Decimal("1000000000000.00")

def normalize_amount_str(value: str) -> str:
    """
    Strips leading zeros completely while preserving decimals and sign.
    
    Examples:
    '00000000000000000000000000000000000000000000815180712' -> '815180712'
    '000080.5000' -> '80.5000'
    '000.00' -> '0.00'
    """
    val = value.strip()
    if not val:
        return "0"
    
    is_negative = val.startswith("-")
    if is_negative or val.startswith("+"):
        val = val[1:]

    # Remove leading zeros before decimal point
    if "." in val:
        integer_part, decimal_part = val.split(".", 1)
        integer_part = integer_part.lstrip("0") or "0"
        clean_val = f"{integer_part}.{decimal_part}"
    else:
        clean_val = val.lstrip("0") or "0"

    if is_negative and clean_val not in ("0", "0.0"):
        clean_val = f"-{clean_val}"
        
    return clean_val


def format_amount(
    value: Union[Decimal, float, str, int, None],
    precision: int = 2,
    as_string: bool = True
) -> Optional[Union[str, Decimal]]:
    """
    Global monetary utility formatter.

    - Accepts Decimal, float, str, int, or None.
    - Removes leading zeros completely.
    - Limits precision to a fixed number of decimal places (default 2).
    - Returns clean string representation e.g. "80.00" (or Decimal if as_string=False).
    """
    if value is None:
        return None

    try:
        if isinstance(value, str):
            clean_str = normalize_amount_str(value)
            d = Decimal(clean_str)
        elif isinstance(value, (float, int)):
            d = Decimal(str(value))
        elif isinstance(value, Decimal):
            d = Decimal(normalize_amount_str(str(value)))
        else:
            d = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        d = Decimal("0.00")

    quantum = Decimal("10") ** -precision
    quantized = d.quantize(quantum, rounding=ROUND_HALF_UP)

    if as_string:
        return f"{quantized:.{precision}f}"
    return quantized


def parse_and_validate_amount(
    value: Any,
    min_value: Optional[Decimal] = Decimal("0.00"),
    max_value: Optional[Decimal] = MAX_MONETARY_LIMIT
) -> Optional[Decimal]:
    """
    Validates and converts input into a high-precision Decimal.
    Rejects malformed strings, negative values (if min_value set), and unrealistic huge numbers.
    """
    if value is None:
        return None

    if isinstance(value, str):
        clean_str = normalize_amount_str(value)
        try:
            d = Decimal(clean_str)
        except InvalidOperation:
            raise ValueError(f"Invalid monetary numeric string: '{value}'")
    elif isinstance(value, (int, float, Decimal)):
        d = Decimal(str(value))
    else:
        raise ValueError(f"Unsupported amount type: {type(value)}")

    if min_value is not None and d < min_value:
        raise ValueError(f"Amount '{d}' must be greater than or equal to {min_value}")

    if max_value is not None and d > max_value:
        raise ValueError(f"Amount '{d}' exceeds maximum allowed limit of {max_value}")

    # Standardize precision to 4 decimal places internally for DB storage/calculations
    return d.quantize(Decimal("0.0001"), rounding=ROUND_HALF_UP)


# Pydantic v2 Custom Reusable Type for Monetary Fields in Schemas/DTOs
MoneyAmount = Annotated[
    Decimal,
    BeforeValidator(parse_and_validate_amount),
    PlainSerializer(
        lambda v: format_amount(v, precision=2, as_string=True),
        return_type=Optional[str],
        when_used="json"
    ),
    WithJsonSchema({
        "type": "string",
        "example": "80.00",
        "description": "Monetary amount formatted as a clean decimal string with fixed 2 decimal places"
    })
]
