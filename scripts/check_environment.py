"""Report Python, locked dependencies, local data/model and inference readiness."""

from __future__ import annotations

import argparse
import importlib.metadata
import json
import os
import pathlib
import platform
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
PACKAGES = ("datafusion", "fastexcel", "huggingface-hub", "mistralrs", "polars")
MODEL = ROOT / "models" / "qwen3.5-9b-q4" / "Qwen3.5-9B-Q4_K_M.gguf"


def collect() -> dict:
    packages = {}
    for name in PACKAGES:
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    return {
        "python": sys.version.split()[0],
        "python_supported": (3, 10) <= sys.version_info[:2] < (3, 14),
        "platform": platform.platform(),
        "packages": packages,
        "uv": shutil.which("uv"),
        "llama_cpp": shutil.which("llama-cli") or shutil.which("llama"),
        "data": {
            name: (ROOT / name / "questions.jsonl").is_file()
            for name in ("train", "public_test")
        },
        "model": {"path": str(MODEL), "present": MODEL.is_file(),
                  "bytes": MODEL.stat().st_size if MODEL.is_file() else None},
        "runtime_ready": (ROOT / "src" / "datamate" / "__main__.py").is_file(),
        "memory_goal": os.environ.get("DATAMATE_MEMORY_GOAL", "not set"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, help="Optional JSON report path.")
    args = parser.parse_args()
    report = collect()
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    missing = [name for name, version in report["packages"].items() if version is None]
    if missing:
        print(f"Missing project dependencies: {', '.join(missing)}", file=sys.stderr)
        return 1
    if not report["runtime_ready"]:
        print("Inference runtime is not built yet (src/datamate entrypoint missing).", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
