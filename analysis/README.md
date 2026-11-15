# Exploratory analysis

This directory holds one-off Python investigations used while reviewing the
competition questions and source files. Question inspections are grouped under
`analysis/questions.py`; source-file inspections are grouped under
`analysis/sources.py`. Run `uv run python -m analysis.questions --help` or
`uv run python -m analysis.sources --help` to see the available commands.

These commands are exploratory utilities, not runtime modules or a supported test
suite. Some read local `train/` data and write generated summaries under
`artifacts/analysis/`. Keep source data, labels and derived row-level artifacts out
of commits.
