"""Schemas Pydantic pour les steps de la pipeline."""
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


# Fonctions d'aggregation autorisees
AggregateFunction = Literal["sum", "count", "count_distinct", "avg", "min", "max"]


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