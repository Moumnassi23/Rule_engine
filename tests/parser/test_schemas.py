"""Tests des schemas Pydantic."""
import pytest
from pydantic import ValidationError

from rule_engine.parser.schemas import (
    AggregateStep,
    ConditionGroup,
    InputDef,
    LeafCondition,
    Metric,
    RuleMetadata,
)


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



# === Tests pour LeafCondition ===

def test_leaf_condition_valid() -> None:
    """Une LeafCondition avec column/operator/value est correctement creee."""
    c = LeafCondition(column="etat", operator="==", value="VALIDE")
    
    assert c.column == "etat"
    assert c.operator == "=="
    assert c.value == "VALIDE"
    assert c.values is None


def test_leaf_condition_invalid_operator() -> None:
    """Un operateur inconnu leve ValidationError."""
    with pytest.raises(ValidationError, match="type=literal_error"):
        LeafCondition(column="etat", operator="EQUAL", value="VALIDE")


# === Tests pour ConditionGroup ===

def test_condition_group_simple() -> None:
    """Un groupe AND avec 2 feuilles contient 2 LeafCondition."""
    g = ConditionGroup(
        logical="AND",
        conditions=[
            {"column": "etat", "operator": "==", "value": "VALIDE"},
            {"column": "solde", "operator": ">=", "value": 1000},
        ],
    )
    
    assert g.logical == "AND"
    assert len(g.conditions) == 2
    assert isinstance(g.conditions[0], LeafCondition)
    assert isinstance(g.conditions[1], LeafCondition)


def test_condition_group_nested() -> None:
    """Un groupe AND contenant un sous-groupe OR est bien parse recursivement."""
    g = ConditionGroup(
        logical="AND",
        conditions=[
            {"column": "etat", "operator": "==", "value": "VALIDE"},
            {
                "logical": "OR",
                "conditions": [
                    {"column": "type", "operator": "==", "value": "COURANT"},
                    {"column": "type", "operator": "==", "value": "EPARGNE"},
                ],
            },
        ],
    )
    
    # L'enfant 0 est une feuille
    assert isinstance(g.conditions[0], LeafCondition)
    
    # L'enfant 1 est un groupe OR
    assert isinstance(g.conditions[1], ConditionGroup)
    assert g.conditions[1].logical == "OR"
    assert len(g.conditions[1].conditions) == 2


def test_condition_group_invalid_logical() -> None:
    """Un logical autre que AND/OR leve ValidationError."""
    with pytest.raises(ValidationError, match="type=literal_error"):
        ConditionGroup(logical="XOR", conditions=[])


def test_condition_group_deep_nesting() -> None:
    """Une imbrication a 3 niveaux est correctement parsee."""
    g = ConditionGroup(
        logical="AND",
        conditions=[
            {"column": "a", "operator": "==", "value": 1},
            {
                "logical": "OR",
                "conditions": [
                    {"column": "b", "operator": "==", "value": 2},
                    {
                        "logical": "AND",
                        "conditions": [
                            {"column": "c", "operator": "==", "value": 3},
                            {"column": "d", "operator": "==", "value": 4},
                        ],
                    },
                ],
            },
        ],
    )
    
    # Navigue jusqu'au niveau 3
    niveau_3 = g.conditions[1].conditions[1]
    
    assert isinstance(niveau_3, ConditionGroup)
    assert niveau_3.logical == "AND"
    assert len(niveau_3.conditions) == 2
    assert niveau_3.conditions[0].column == "c"


def test_aggregate_step_valid() -> None:
    """Un AggregateStep valide cree les Metric correctement."""
    agg = AggregateStep(
        type="aggregate",
        group_by=["tier_id"],
        metrics=[
            {"name": "solde_total", "function": "sum", "column": "solde"},
        ],
    )

    assert agg.type == "aggregate"
    assert agg.group_by == ["tier_id"]
    assert len(agg.metrics) == 1
    assert isinstance(agg.metrics[0], Metric)
    assert agg.metrics[0].function == "sum"


def test_aggregate_step_invalid_type() -> None:
    """type='agg' au lieu de 'aggregate' leve ValidationError."""
    with pytest.raises(ValidationError, match="type=literal_error"):
        AggregateStep(
            type="agg",
            group_by=["x"],
            metrics=[{"name": "n", "function": "sum", "column": "c"}],
        )


# À toi : test_aggregate_step_invalid_function et test_aggregate_step_empty_group_by

def test_aggregate_step_invalid_function() -> None:
    """Une function d'aggregation inconnue leve ValidationError."""
    with pytest.raises(ValidationError, match="type=literal_error"):
        AggregateStep(
            type="aggregate",
            group_by=["tier_id"],
            metrics=[
                {"name": "solde_median", "function": "median", "column": "solde"},
            ],
        )


def test_aggregate_step_empty_group_by() -> None:
    """Un group_by vide leve ValidationError."""
    with pytest.raises(ValidationError, match="type=too_short"):
        AggregateStep(
            type="aggregate",
            group_by=[],
            metrics=[{"name": "n", "function": "sum", "column": "c"}],
        )