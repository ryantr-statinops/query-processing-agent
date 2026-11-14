"""Compatibility CLI for the archived purchase-intent benchmark."""

if __name__ == "__main__":
    import os

    os.environ["POLARS_MAX_THREADS"] = "1"
    from scripts.legacy.benchmark_purchase_intent import main

    raise SystemExit(main())
else:
    from scripts.legacy.benchmark_purchase_intent import *
