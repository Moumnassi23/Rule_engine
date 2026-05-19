"""Point d'entree public du parser : parse_rule(path) -> Rule."""
from pathlib import Path

from pydantic import ValidationError

from rule_engine.parser.exceptions import RuleSchemaError
from rule_engine.parser.loader import load_rule_file
from rule_engine.parser.schemas import Rule


def parse_rule(path: str | Path) -> Rule:
    """Charge et valide un fichier YAML de regle.

    Cette fonction est le point d'entree public du parser. Elle combine :
    - Le chargement et la validation YAML (via load_rule_file)
    - La validation Pydantic de la structure metier (via Rule)

    Args:
        path: chemin vers le fichier YAML de la regle (str ou Path)

    Returns:
        Une instance Rule validee, prete a etre utilisee par le runner.

    Raises:
        RuleLoadError: si le fichier n'existe pas, n'est pas lisible,
                       n'est pas un YAML valide, ou ne contient pas un dict.
        RuleSchemaError: si le contenu du YAML ne respecte pas la structure
                         attendue (champ manquant, type incorrect, etc.).
    """
    # 1. Chargement du fichier YAML -> dict Python
    # Peut lever RuleLoadError (propage directement)
    data = load_rule_file(path)

    # 2. Validation Pydantic du dict -> objet Rule
    # Si ValidationError de Pydantic, on la convertit en RuleSchemaError
    try:
        return Rule(**data)
    except ValidationError as e:
        raise RuleSchemaError(
            f"Le fichier {path} ne respecte pas la structure attendue :\n{e}"
        ) from e