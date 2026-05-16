from pydantic import BaseModel, ConfigDict


class InputDef(BaseModel):
    """Définition d'un input d'une règle (un DataFrame fourni par le job)."""
    model_config = ConfigDict(extra="forbid")  # Forbid extra fields not defined in the model

    name: str # nom logique utilisé dans le pipeline (ex: "compte")
    table: str  # nom de la table source (ex: "silver.compte"), documentaire




