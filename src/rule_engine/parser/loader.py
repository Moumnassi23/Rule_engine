"""
Loader : lit un fichier YAML et retourne son contenu sous forme de dict.

Ce module ne fait que la lecture et la validation de base (fichier existe,
YAML valide, racine = dict). La validation du contenu metier est faite par
les modules schemas.py et validator.py.
"""
from pathlib import Path

import yaml

from rule_engine.parser.exceptions import RuleLoadError


def load_rule_file(path: str | Path) -> dict:
    """
    Charge un fichier YAML de regle et retourne son contenu sous forme de dict.

    Args:
        path: chemin vers le fichier YAML (str ou Path)

    Returns:
        Le contenu du YAML sous forme de dict Python.

    Raises:
        RuleLoadError: si le fichier n'existe pas, n'est pas un fichier,
                       n'est pas un YAML valide, ou ne contient pas un dict.
    """
    p = Path(path)

    # 1. Verifier que le fichier existe et est bien un fichier
    if not p.exists():
        raise RuleLoadError(f"Fichier introuvable : {p}")
    if not p.is_file():
        raise RuleLoadError(f"Le chemin n'est pas un fichier : {p}")

    # 2. Lire et parser le YAML
    try:
        with p.open(encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise RuleLoadError(f"YAML invalide dans {p} : {e}") from e

    # 3. Verifier que le contenu est bien un dict
    if not isinstance(data, dict):
        raise RuleLoadError(
            f"Le fichier {p} doit contenir un dict a la racine, "
            f"trouve : {type(data).__name__}"
        )

    return data