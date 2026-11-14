"""Compatibility CLI for the archived candidate collector."""

from scripts.legacy.collect_candidates import *
from scripts.legacy.collect_candidates import main


if __name__ == "__main__":
    raise SystemExit(main())
