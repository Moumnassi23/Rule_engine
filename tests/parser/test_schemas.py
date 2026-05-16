"""Tests des schemas Pydantic."""
import pytest
from pydantic import ValidationError

from rule_engine.parser.schemas import InputDef


def test_input_def_valid() -> None:
    """Un InputDef valide est correctement instancie."""
    inp = InputDef(name="compte", table="silver.compte")

    assert inp.name == "compte"
    assert inp.table == "silver.compte"


def test_input_def_missing_table() -> None:
    """Un InputDef sans le champ 'table' doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="type=missing"):
        InputDef(name="compte")


def test_input_def_invalid_type() -> None:
    """Un InputDef avec un type incorrect doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="type=string_type"):
        InputDef(name="compte", table=123)


def test_input_def_extra_field() -> None:
    """Un InputDef avec un champ inconnu doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="type=extra_forbidden"):
        InputDef(name="compte", table="silver.compte", extra_field="oups")