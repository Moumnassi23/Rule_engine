"""Schema Pydantic racine : Rule (assemble metadata + inputs + pipeline)."""
from pydantic import Field

from rule_engine.parser.schemas.inputs import InputDef
from rule_engine.parser.schemas.metadata import RuleMetadata
from rule_engine.parser.schemas.pipeline import Pipeline


class Rule(RuleMetadata):
    """Une regle complete : metadonnees + inputs + pipeline.

    Herite de RuleMetadata pour reutiliser :
    - Les 5 champs version, description, rule_date, exec_date, commit_id
    - Le validator @field_validator sur exec_date
    - La config extra='forbid'

    Ajoute :
    - inputs : liste des DataFrames attendus (au moins 1)
    - pipeline : la pipeline de transformation
    """

    inputs: list[InputDef] = Field(min_length=1)
    pipeline: Pipeline