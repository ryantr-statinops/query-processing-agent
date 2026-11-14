"""Compatibility CLI for datamate.data.catalog_audit.review."""
from pathlib import Path

from datamate.data.catalog_audit.review import main


if __name__ == "__main__":
    main(repo_root=Path(__file__).resolve().parents[1])
