"""Compatibility CLI for the archived experiment evaluator."""

from scripts.legacy.evaluate_experiment import *
from scripts.legacy.evaluate_experiment import main


if __name__ == "__main__":
    raise SystemExit(main())
