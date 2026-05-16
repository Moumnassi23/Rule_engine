from typing import Literal, Union
from pydantic import BaseModel, ConfigDict


Value_type = Union[str, int, float, bool]


class LeafCondition(BaseModel):
    """Une condition atomique : column, operator, value (ou values pour in/not_in)."""

    model_config = ConfigDict(extra="forbid")

    column: str
    operator: Literal["==", "!=", ">", "<", ">=", "<=", "in", "not_in", "is_null", "is_not_null"]
    value: Value_type | None = None
    values: list[Value_type] | None = None


class ConditionGroup(BaseModel):

    """Un groupe de conditions, avec un opérateur logique (AND/OR) et une liste de conditions enfants."""

    model_config = ConfigDict(extra="forbid")

    logical: Literal["AND", "OR"]
    conditions: list[Union[LeafCondition, "ConditionGroup"]]


Condition = Union[LeafCondition, "ConditionGroup"]


# Finalisation des forward references
ConditionGroup.model_rebuild()
