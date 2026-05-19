"""Schema Pydantic pour la pipeline d'une regle."""
from pydantic import BaseModel, ConfigDict, Field

from rule_engine.parser.schemas.steps import Step


class Pipeline(BaseModel):
    """La pipeline de transformation : une liste ordonnee de steps."""

    model_config = ConfigDict(extra="forbid")

    steps: list[Step] = Field(min_length=1)