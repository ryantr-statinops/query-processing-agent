#!/bin/sh
set -eu

exec uv run --locked --no-sync python -m datamate --data-root /data --result-root /result
