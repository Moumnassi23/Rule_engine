"""
Exceptions custom du parser de regles.

Toutes les exceptions levees par le parser heritent de ParserError,
ce qui permet de les attraper toutes d'un coup avec un seul `except`,
ou individuellement selon le contexte.
"""

class ParserError(Exception):
    """Base class for exceptions in the rule parser."""
    pass


class RuleLoadError(ParserError):
    """Raised when there is an error loading the rule file."""
    pass


class RuleSchemaError(ParserError):
    """Raised when the rule file does not conform to the expected schema."""
    pass


class RuleValidationError(ParserError):
    """Raised when the rule file fails validation."""
    pass

