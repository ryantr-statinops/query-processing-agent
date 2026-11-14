"""Compatibility CLI for the archived deterministic evaluator."""

from scripts.legacy.evaluate_deterministic_dev import *
from scripts.legacy.evaluate_deterministic_dev import main


if __name__ == "__main__":
    raise SystemExit(main())
