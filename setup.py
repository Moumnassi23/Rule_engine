"""Setup minimal pour rendre rule_engine importable comme un package Python."""
from setuptools import setup, find_packages

setup(
    name="rule-engine",
    version="0.1.0",
    description="Moteur de regles declaratif pour transformations PySpark CDM",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.10",
)
