#!/bin/sh
set -eu

exec uv run --locked --no-sync python /code/src/runner.py --data-root /data --result-root /result
