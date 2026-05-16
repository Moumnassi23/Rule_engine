"""Tests des schemas Pydantic."""
import pytest
from pydantic import ValidationError

from rule_engine.parser.schemas import InputDef
from rule_engine.parser.schemas.metadata import RuleMetadata


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


def test_rule_metadata_valid_full()->None:
    """Un RuleMetadata complet et valide est correctement instancie."""
    metadata = RuleMetadata(
        version="1.0.0",
        description="Ceci est une regle de test valide.",
        rule_date="2024-01-01",
        exec_date="2024-02-01",
        commit_id="abc123",
    )

    assert metadata.version == "1.0.0"
    assert metadata.description == "Ceci est une regle de test valide."
    assert metadata.rule_date.isoformat() == "2024-01-01"
    assert metadata.exec_date == "2024-02-01"
    assert metadata.commit_id == "abc123"


def test_rule_metadata_valid_placeholde()->None:
    """Un RuleMetadata avec exec_date en placeholder est valide."""
    metadata = RuleMetadata(
        version="1.0.0",
        description="Ceci est une regle de test valide.",
        rule_date="2024-01-01",
        exec_date="${runtime_date}",
    )

    assert metadata.exec_date == "${runtime_date}"


def test_rule_metadata_invalid_versio()->None:
    """Un RuleMetadata avec une version mal formée doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="pattern"):
        RuleMetadata(
            version="1.0",  # version invalide
            description="Ceci est une regle de test valide.",
            rule_date="2024-01-01",
            exec_date="2024-02-01",
        )


def test_rule_metadata_description_too_short()->None:
    """Un RuleMetadata avec une description trop courte doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="at least 10 characters"):
        RuleMetadata(
            version="1.0.0",
            description="rea",  # description trop courte
            rule_date="2024-01-01",
            exec_date="2024-02-01",
        )


def test_rule_metadata_invalid_exec_date()->None:
    """Un RuleMetadata avec exec_date ni date ISO ni placeholder doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="exec_date doit etre une date ISO"):
        RuleMetadata(
            version="1.0.0",
            description="Ceci est une regle de test valide.",
            rule_date="2024-01-01",
            exec_date="invalid_date",  # exec_date invalide
        )


def test_rule_metadata_invalid_rule_date()->None:
    """Un RuleMetadata avec rule_date non ISO doit lever une ValidationError."""
    with pytest.raises(ValidationError, match="type=date_from_datetime_parsing"):
        RuleMetadata(
            version="1.0.0",
            description="Ceci est une regle de test valide.",
            rule_date="01-01-2024",  # rule_date invalide
            exec_date="2024-02-01",
        )


