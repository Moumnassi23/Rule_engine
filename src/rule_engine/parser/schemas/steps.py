"""Schemas Pydantic pour les steps de la pipeline."""
from typing import Annotated, Literal, Union
from pydantic import BaseModel, ConfigDict, Field, model_validator
from rule_engine.parser.schemas.conditions import Condition, ValueType, ConditionGroup


# Fonctions d'aggregation autorisees
AggregateFunction = Literal["sum", "count", "count_distinct", "avg", "min", "max"]


# Operateurs autorises pour un filter simple
FilterOperator = Literal[
    "==", "!=", ">", "<", ">=", "<=",
    "in", "not_in",
    "is_null", "is_not_null",
    "like",
]


class Metric(BaseModel):
    """Une metrique d'aggregation : name, function, column."""

    model_config = ConfigDict(extra="forbid")

    name: str
    function: AggregateFunction
    column: str


class AggregateStep(BaseModel):
    """Step d'aggregation : group_by + metrics."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["aggregate"]
    group_by: list[str] = Field(min_length=1)
    metrics: list[Metric] = Field(min_length=1)


class JoinStep(BaseModel):
    """Step de jointure : with, how, broadcast, right_columns."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )

    type: Literal["join"]
    with_table: str = Field(alias="with", min_length=1)
    how: Literal["inner", "left", "right", "full"] = "inner"
    broadcast: bool = False
    right_columns: list[str] | None = None


class FilterStep(BaseModel):
    """Step de filtre. Peut etre simple (column/operator/value) ou multiple (logical/conditions)."""

    model_config = ConfigDict(extra="forbid")

    type: Literal["filter"]

    # Forme A : condition simple a plat (tous optionnels au niveau Pydantic)
    column: str | None = None
    operator: FilterOperator | None = None
    value: ValueType | None = None
    values: list[ValueType] | None = None

    # Forme B/C : conditions multiples avec un operateur logique
    logical: Literal["AND", "OR"] | None = None
    conditions: list[Condition] | None = None

    @model_validator(mode="after")
    def check_form_coherence(self) -> "FilterStep":
        """Verifie qu'on a UN seul des deux formats : simple OU multiple."""
        has_simple_form = self.column is not None
        has_multiple_form = self.conditions is not None

        if has_simple_form and has_multiple_form:
            raise ValueError(
                "Un filter ne peut pas avoir a la fois une condition simple "
                "(column/operator/value) et un bloc conditions. Choisir l'un ou l'autre."
            )

        if not has_simple_form and not has_multiple_form:
            raise ValueError(
                "Un filter doit avoir soit une condition simple "
                "(column/operator/value), soit un bloc conditions."
            )

        if has_simple_form and self.operator is None:
            raise ValueError(
                "Pour une condition simple, 'operator' est obligatoire."
            )

        if has_multiple_form and self.logical is None:
            raise ValueError(
                "Pour un bloc conditions, 'logical' est obligatoire."
            )

        return self


# Finalisation des forward references pour FilterStep
# (FilterStep utilise Condition qui contient une forward ref vers ConditionGroup)
Step = Annotated[
    Union[FilterStep, JoinStep, AggregateStep],
    Field(discriminator="type"),
]

FilterStep.model_rebuild()