#!/bin/sh
set -eu

uv run --locked --no-sync python -m datamate --data-root /data --result-root /result

if [ -f /result/submission.jsonl ] && [ ! -f /result/answer.jsonl ]; then
    cp -f /result/submission.jsonl /result/answer.jsonl
fi
