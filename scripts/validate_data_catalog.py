"""Validate catalog artifacts and run repository-level checks."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys

from datamate.data.catalog_audit import review
from datamate.data.catalog_audit.validate import (
    CatalogValidationError,
    handoff,
    require,
    validate,
)


ROOT = Path(__file__).resolve().parents[1]


def run_repository_checks(output: Path, result: dict, *, repo_root: Path) -> dict:
    """Run Git and unittest checks outside the reusable catalog package."""
    try:
        initial_public = subprocess.check_output(
            ["git", "show", "HEAD:docs/data-schema-catalog.md"], cwd=repo_root
        ).decode("utf-8").split("## public_test", 1)[1]
    except (subprocess.SubprocessError, OSError, IndexError, UnicodeDecodeError) as error:
        raise CatalogValidationError(f"Cannot read the tracked public_test catalog section: {error}") from error

    current_doc = (repo_root / "docs/data-schema-catalog.md").read_text(encoding="utf-8")
    require(
        initial_public.strip() == current_doc.split("## public_test", 1)[1].strip(),
        "The public_test section of docs/data-schema-catalog.md changed.",
    )
    result["public_test_document_unchanged"] = True

    whitespace = subprocess.run(
        ["git", "diff", "--check"], cwd=repo_root, capture_output=True, text=True
    )
    require(whitespace.returncode == 0, whitespace.stdout + whitespace.stderr)
    result["git_diff_check"] = "passed"

    test_command = [
        sys.executable,
        "-m",
        "unittest",
        "discover",
        "-s",
        "tests",
        "-p",
        "*catalog*.py",
        "-v",
    ]
    test_run = subprocess.run(
        test_command,
        cwd=repo_root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    (output / "catalog_tests.log").write_text(
        test_run.stdout + test_run.stderr, encoding="utf-8"
    )
    require(test_run.returncode == 0, test_run.stderr)
    test_count = re.search(r"Ran (\d+) tests?", test_run.stderr)
    result["synthetic_tests"] = {
        "status": "passed",
        "count": int(test_count[1]) if test_count else None,
        "log": "artifacts/data_prep/catalog_tests.log",
    }
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "artifacts/data_prep")
    parser.add_argument("--write-report", action="store_true")
    args = parser.parse_args(argv)
    output = args.output.resolve()

    try:
        result = validate(output, repo_root=ROOT)
        result = run_repository_checks(output, result, repo_root=ROOT)
        review.dump_json(output / "catalog_validation.json", result)
        if args.write_report:
            git_state = subprocess.check_output(
                ["git", "status", "--short"], cwd=ROOT
            ).decode("utf-8").strip()
            handoff(
                review.load_json(output / "data_catalog.json"),
                result,
                repo_root=ROOT,
                git_state=git_state,
            )
        print(json.dumps(result))
        return 0
    except (CatalogValidationError, OSError, subprocess.SubprocessError, ValueError, IndexError) as error:
        print(f"Catalog validation failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
