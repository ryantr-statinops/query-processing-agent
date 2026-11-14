"""Run the available DataMate preparation and readiness scripts in order."""

from __future__ import annotations

import argparse
import datetime
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
REPORT = ROOT / "artifacts" / "preparation_report.json"


def run_step(name: str, arguments: list[str] | None = None) -> dict:
    command = [sys.executable, str(SCRIPTS / name), *(arguments or [])]
    print(f"\n=== {name} ===", flush=True)
    result = subprocess.run(command, cwd=ROOT, check=False)
    return {"script": name, "command": command, "exit_code": result.returncode}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skip-data-setup", action="store_true", help="Use data already extracted locally.")
    parser.add_argument("--skip-model-download", action="store_true", help="Skip the approximately 5.68 GB model download/check.")
    parser.add_argument("--data-only", action="store_true", help="Prepare and inspect data without downloading model weights.")
    parser.add_argument("--report", type=pathlib.Path, default=REPORT, help="JSON run report (default: artifacts/preparation_report.json).")
    args = parser.parse_args()

    steps = []
    if not args.skip_data_setup:
        steps.append(run_step("setup_data.py"))
    steps.append(run_step("inspect_data.py", ["--output", str(ROOT / "artifacts" / "data_inspection.json")]))
    if not args.data_only and not args.skip_model_download:
        steps.append(run_step("download_model.py"))
    steps.append(run_step("check_environment.py", ["--output", str(ROOT / "artifacts" / "environment.json")]))

    blockers = [step for step in steps if step["exit_code"] != 0]
    report = {
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "steps": steps,
        "ok": not blockers,
        "inference_available": (ROOT / "src" / "datamate" / "__main__.py").is_file(),
        "note": "Preparation only; inference and evaluation require the rebuilt datamate runtime.",
    }
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"\nPreparation report: {args.report}")
    if blockers:
        print(f"Pipeline stopped with {len(blockers)} failed step(s).", file=sys.stderr)
        return 1
    print("Preparation steps completed.")
    if not report["inference_available"]:
        print("Inference/evaluation are pending the rebuilt src/datamate runtime.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
