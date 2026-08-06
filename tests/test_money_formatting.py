import pytest
from decimal import Decimal
from pydantic import BaseModel
from app.common.utils.money import (
    format_amount,
    normalize_amount_str,
    parse_and_validate_amount,
    MoneyAmount
)


class DummySchema(BaseModel):
    amount: MoneyAmount
    balance: MoneyAmount


def test_normalize_amount_str_leading_zeros():
    malformed = "00000000000000000000000000000000000000000000815180712"
    normalized = normalize_amount_str(malformed)
    assert normalized == "815180712"


def test_normalize_amount_str_with_decimal():
    malformed = "000080.5000"
    normalized = normalize_amount_str(malformed)
    assert normalized == "80.5000"


def test_format_amount_fixed_precision():
    assert format_amount("80") == "80.00"
    assert format_amount("80.5") == "80.50"
    assert format_amount(Decimal("80.567")) == "80.57"
    assert format_amount(0.1 + 0.2) == "0.30"
    assert format_amount("00000000000000000000000000000000000000000000815180712") == "815180712.00"


def test_parse_and_validate_amount_success():
    d = parse_and_validate_amount("000150.7500")
    assert isinstance(d, Decimal)
    assert d == Decimal("150.7500")


def test_parse_and_validate_amount_rejects_malformed_string():
    with pytest.raises(ValueError, match="Invalid monetary numeric string"):
        parse_and_validate_amount("invalid_amount_123")


def test_parse_and_validate_amount_rejects_negative():
    with pytest.raises(ValueError, match="must be greater than or equal to"):
        parse_and_validate_amount("-50.00")


def test_parse_and_validate_amount_rejects_extreme_value():
    with pytest.raises(ValueError, match="exceeds maximum allowed limit"):
        parse_and_validate_amount("1000000000001.00")


def test_pydantic_schema_money_serialization():
    instance = DummySchema(
        amount="00000000000000000000000000000000000000000000815180712",
        balance=Decimal("100.5")
    )
    # Json serialization output
    json_output = instance.model_dump(mode="json")
    assert json_output["amount"] == "815180712.00"
    assert json_output["balance"] == "100.50"
