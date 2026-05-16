"""Schemas Pydantic pour les metadonnees d'une regle."""
from datetime import date

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RuleMetadata(BaseModel):
    """Metadonnees d'une regle (version, description, dates, commit_id)."""

    model_config = ConfigDict(extra="forbid")

    # === Champs ===
    version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    description: str = Field(min_length=10)
    rule_date: date
    exec_date: str
    commit_id: str = Field(default="")

    # === Validators ===
    @field_validator("exec_date")
    @classmethod
    def validate_exec_date(cls, value: str) -> str:
        # Cas 1 : placeholder runtime (${...})
        if value.startswith("${") and value.endswith("}"):
            return value

        # Cas 2 : date ISO valide
        try:
            date.fromisoformat(value)
            return value
        except ValueError as e:
            raise ValueError(
                f"exec_date doit etre une date ISO (YYYY-MM-DD) ou un placeholder "
                f"${{...}}, recu : {value!r}"
            ) from e