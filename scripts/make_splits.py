"""Compatibility CLI for the archived split-manifest writer."""

from scripts.legacy.make_splits import *
from scripts.legacy.make_splits import main


if __name__ == "__main__":
    raise SystemExit(main())
