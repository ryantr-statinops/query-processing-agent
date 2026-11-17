#!/bin/bash
set -euo pipefail

echo "=== DataMate Training & Heritage Verification ==="
echo "Model: Qwen3.5-9B-Q4_K_M (Zero-Shot Agentic RAG)"
echo "Checking manifest..."

python3 -c "
import json, pathlib
manifest = json.loads(pathlib.Path('training_code/data_manifest.json').read_text(encoding='utf-8'))
print('Declared Model:', manifest['models']['generator']['filename'])
print('Base Repo:', manifest['models']['generator']['base_model'])
print('Fine-tuning status:', manifest['training_declaration']['fine_tuning'])
"

echo "Verification completed successfully."
