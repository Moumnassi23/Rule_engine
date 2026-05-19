"""Tests des schemas Pydantic."""
import pytest
from pydantic import ValidationError

from rule_engine.parser.schemas import (
    AggregateStep,
    ConditionGroup,
    InputDef,
    JoinStep,            
    LeafCondition,
    Metric,
    RuleMetadata,
    FilterStep,
    Step,
    Pipeline
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


# === Tests pour JoinStep ===

def test_join_step_valid_with_alias() -> None:
    """Un JoinStep instancie avec l'alias 'with' (depuis YAML) fonctionne."""
    join = JoinStep(**{
        "type": "join",
        "with": "tier",
        "how": "left",
        "broadcast": True,
    })

    assert join.with_table == "tier"
    assert join.how == "left"
    assert join.broadcast is True


def test_join_step_default_values() -> None:
    """Les valeurs par defaut sont appliquees quand non specifiees."""
    join = JoinStep(**{"type": "join", "with": "tier"})

    assert join.how == "inner"
    assert join.broadcast is False
    assert join.right_columns is None


def test_join_step_with_right_columns() -> None:
    """right_columns optionnel est bien parse."""
    join = JoinStep(**{
        "type": "join",
        "with": "tier",
        "right_columns": ["tier_id", "tier_nom"],
    })

    assert join.right_columns == ["tier_id", "tier_nom"]


def test_join_step_populate_by_name() -> None:
    """Le nom Python 'with_table' est aussi accepte (grace a populate_by_name)."""
    join = JoinStep(type="join", with_table="tier")

    assert join.with_table == "tier"


def test_join_step_invalid_how() -> None:
    """how='cross' (non autorise) leve ValidationError."""
    with pytest.raises(ValidationError, match="type=literal_error"):
        JoinStep(**{"type": "join", "with": "tier", "how": "cross"})


def test_join_step_empty_with() -> None:
    """with vide (chaine vide) leve ValidationError."""
    with pytest.raises(ValidationError, match="type=string_too_short"):
        JoinStep(**{"type": "join", "with": ""})


# === Tests pour FilterStep ===

def test_filter_step_simple_form() -> None:
    """Forme A : condition simple a plat."""
    f = FilterStep(type="filter", column="etat", operator="==", value="VALIDE")

    assert f.column == "etat"
    assert f.operator == "=="
    assert f.value == "VALIDE"
    assert f.conditions is None


def test_filter_step_multiple_form() -> None:
    """Forme B : conditions multiples avec logical."""
    f = FilterStep(
        type="filter",
        logical="AND",
        conditions=[
            {"column": "etat", "operator": "==", "value": "VALIDE"},
            {"column": "solde", "operator": ">=", "value": 1000},
        ],
    )

    assert f.logical == "AND"
    assert len(f.conditions) == 2
    assert f.column is None


def test_filter_step_nested_form() -> None:
    """Forme C : conditions imbriquees (recursion)."""
    f = FilterStep(
        type="filter",
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

    assert isinstance(f.conditions[1], ConditionGroup)
    assert f.conditions[1].logical == "OR"


def test_filter_step_mixed_forms_rejected() -> None:
    """Melanger forme simple et forme multiple leve ValidationError."""
    with pytest.raises(ValidationError, match="ne peut pas avoir a la fois"):
        FilterStep(
            type="filter",
            column="etat",
            operator="==",
            value="VALIDE",
            logical="AND",
            conditions=[],
        )


def test_filter_step_no_form_rejected() -> None:
    """Un filter sans aucune forme leve ValidationError."""
    with pytest.raises(ValidationError, match="doit avoir soit"):
        FilterStep(type="filter")


def test_filter_step_simple_without_operator() -> None:
    """Forme simple sans operator leve ValidationError."""
    with pytest.raises(ValidationError, match="'operator' est obligatoire"):
        FilterStep(type="filter", column="etat")


def test_filter_step_multiple_without_logical() -> None:
    """Forme multiple sans logical leve ValidationError."""
    with pytest.raises(ValidationError, match="'logical' est obligatoire"):
        FilterStep(
            type="filter",
            conditions=[{"column": "x", "operator": "==", "value": 1}],
        )

# === Tests pour l'union discriminee Step ===

def test_step_discriminator_filter() -> None:
    """Un dict avec type='filter' est parse comme FilterStep."""
    from pydantic import TypeAdapter

    validator = TypeAdapter(Step)
    s = validator.validate_python({
        "type": "filter",
        "column": "etat",
        "operator": "==",
        "value": "VALIDE",
    })

    assert isinstance(s, FilterStep)


def test_step_discriminator_join() -> None:
    """Un dict avec type='join' est parse comme JoinStep."""
    from pydantic import TypeAdapter

    validator = TypeAdapter(Step)
    s = validator.validate_python({"type": "join", "with": "tier"})

    assert isinstance(s, JoinStep)
    assert s.with_table == "tier"


def test_step_discriminator_unknown_type() -> None:
    """Un type inconnu leve ValidationError avec un message clair."""
    from pydantic import TypeAdapter

    validator = TypeAdapter(Step)

    with pytest.raises(ValidationError, match="type=union_tag_invalid"):
        validator.validate_python({"type": "unknown"})


# === Tests pour Pipeline ===

def test_pipeline_valid() -> None:
    """Une pipeline avec 3 steps de types differents est parsee correctement."""
    p = Pipeline(steps=[
        {"type": "filter", "column": "etat", "operator": "==", "value": "VALIDE"},
        {"type": "join", "with": "tier"},
        {
            "type": "aggregate",
            "group_by": ["tier_id"],
            "metrics": [{"name": "solde_total", "function": "sum", "column": "solde"}],
        },
    ])

    assert len(p.steps) == 3
    assert isinstance(p.steps[0], FilterStep)
    assert isinstance(p.steps[1], JoinStep)
    assert isinstance(p.steps[2], AggregateStep)


def test_pipeline_empty_rejected() -> None:
    """Une pipeline sans step leve ValidationError."""
    with pytest.raises(ValidationError, match="type=too_short"):
        Pipeline(steps=[])


def test_pipeline_unknown_step_type() -> None:
    """Un step avec un type inconnu leve ValidationError."""
    with pytest.raises(ValidationError, match="type=union_tag_invalid"):
        Pipeline(steps=[{"type": "unknown"}])