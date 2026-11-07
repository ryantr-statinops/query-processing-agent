"""Write the deterministic DataMate business-level split manifest."""

from __future__ import annotations

import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from datamate.data.splits import write_split_manifest  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train-root", type=pathlib.Path, default=ROOT / "train")
    parser.add_argument("--output", type=pathlib.Path, default=ROOT / "configs" / "splits" / "seed_2026.json")
    parser.add_argument("--seed", type=int, default=2026)
    args = parser.parse_args()
    manifest = write_split_manifest(args.train_root, args.output, args.seed)
    print(f"Wrote {args.output}: {len(manifest['holdout_businesses'])} holdout businesses, "
          f"{len(manifest['folds'])} development folds")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
