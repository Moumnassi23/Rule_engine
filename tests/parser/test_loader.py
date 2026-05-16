"""Tests du loader."""
from pathlib import Path

import pytest

from rule_engine.parser.exceptions import RuleLoadError
from rule_engine.parser.loader import load_rule_file


def test_load_valid_yaml(tmp_path: Path) -> None:
    """Un YAML valide est correctement charge en dict."""
    yaml_file = tmp_path / "rule.yaml"
    yaml_file.write_text(
        'version: "1.0.0"\n'
        'description: "test"\n',
        encoding="utf-8",
    )

    result = load_rule_file(yaml_file)

    assert result == {"version": "1.0.0", "description": "test"}


def test_load_missing_file(tmp_path: Path) -> None:
    """Un fichier manquant leve une RuleLoadError."""
    missing = tmp_path / "ce_fichier_nexiste_pas.yaml"
    # On NE crée PAS le fichier
    
    with pytest.raises(RuleLoadError, match="introuvable"):
        load_rule_file(missing)


def test_load_path_is_directory(tmp_path: Path) -> None:
    """Un chemin qui pointe vers un dossier leve une RuleLoadError."""
    # tmp_path EST DEJA un dossier existant fourni par pytest
    with pytest.raises(RuleLoadError, match="pas un fichier"):
        load_rule_file(tmp_path)


def test_load_malformed_yaml(tmp_path:Path)->None:
    """Un YAML invalide leve une RuleLoadError."""
    yaml_file = tmp_path / "invalid.yaml"
    yaml_file.write_text('version: "1.0.0"\ndescription: "test"\ninvalid_yaml', encoding="utf-8")

    with pytest.raises(RuleLoadError, match="YAML invalide"):
        load_rule_file(yaml_file)


def test_load_yaml_not_a_dict(tmp_path: Path) -> None:
    """Un YAML qui ne contient pas un dict a la racine leve une RuleLoadError."""
    yaml_file = tmp_path / "list.yaml"
    yaml_file.write_text('- item1\n- item2\n', encoding="utf-8")

    with pytest.raises(RuleLoadError, match="doit contenir un dict a la racine"):
        load_rule_file(yaml_file)




