"""Schemas Pydantic pour les conditions de filtre."""
from typing import Literal, Union

from pydantic import BaseModel, ConfigDict


# Types primitifs autorises pour les valeurs
ValueType = str | int | float | bool


class LeafCondition(BaseModel):
    """Une condition atomique : column, operator, value (ou values pour in/not_in)."""

    model_config = ConfigDict(extra="forbid")

    column: str
    operator: Literal[
        "==", "!=", ">", "<", ">=", "<=",
        "in", "not_in",
        "is_null", "is_not_null",
        "like",
    ]
    value: ValueType | None = None
    values: list[ValueType] | None = None


class ConditionGroup(BaseModel):
    """Un groupe de conditions combinees par AND ou OR."""

    model_config = ConfigDict(extra="forbid")

    logical: Literal["AND", "OR"]
    conditions: list[Union[LeafCondition, "ConditionGroup"]]


# Type alias pour utilisation externe
Condition = Union[LeafCondition, "ConditionGroup"]


# Finalisation des forward references
ConditionGroup.model_rebuild()