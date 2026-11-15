"""Download and verify Qwen3.5-9B Q4_K_M GGUF weights and tokenizer files.

Run with ``uv run --locked --no-sync python scripts/download_model.py`` after
``uv sync --locked``.
An existing verified file is reused without network access. Hugging Face Hub
resumes its own incomplete downloads when this command is run again.
This prepares weights and tokenizer offline files; it does not configure an inference runtime.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib


REPO_ID = "unsloth/Qwen3.5-9B-GGUF"
REVISION = "3885219b6810b007914f3a7950a8d1b469d598a5"
MODEL_FILE = "Qwen3.5-9B-Q4_K_M.gguf"
MODEL_SIZE = 5_680_522_464
MODEL_SHA256 = "03b74727a860a56338e042c4420bb3f04b2fec5734175f4cb9fa853daf52b7e8"
DEFAULT_OUTPUT = pathlib.Path(__file__).resolve().parents[1] / "models" / "qwen3.5-9b-q4"

TOKENIZER_REPO_ID = "Qwen/Qwen3.5-9B"
TOKENIZER_FILES = [
    "tokenizer.json",
    "tokenizer_config.json",
    "config.json",
    "chat_template.jinja",
    "vocab.json",
    "merges.txt",
]
DEFAULT_TOKENIZER_OUTPUT = pathlib.Path(__file__).resolve().parents[1] / "models" / "qwen3.5-9b-tokenizer"


def verify_model(model_file: pathlib.Path) -> None:
    """Reject incomplete or different weights before reporting success."""
    if model_file.stat().st_size != MODEL_SIZE:
        raise ValueError(f"Model size mismatch: {model_file}. Expected {MODEL_SIZE} bytes.")
    digest = hashlib.sha256()
    with model_file.open("rb") as stream:
        for chunk in iter(lambda: stream.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    if digest.hexdigest() != MODEL_SHA256:
        raise ValueError(f"Model SHA-256 mismatch: {model_file}.")


def download_tokenizer(tokenizer_output: pathlib.Path) -> None:
    """Download required tokenizer files for offline vLLM GGUF execution."""
    from huggingface_hub import hf_hub_download

    tokenizer_output.mkdir(parents=True, exist_ok=True)
    for filename in TOKENIZER_FILES:
        target_file = tokenizer_output / filename
        if target_file.is_file() and target_file.stat().st_size > 0:
            print(f"Existing tokenizer file verified: {target_file.name}", flush=True)
            continue
        print(f"Downloading tokenizer file {TOKENIZER_REPO_ID}/{filename}...", flush=True)
        hf_hub_download(
            repo_id=TOKENIZER_REPO_ID,
            filename=filename,
            local_dir=str(tokenizer_output),
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=pathlib.Path,
        default=DEFAULT_OUTPUT,
        help="Destination directory for GGUF model (default: models/qwen3.5-9b-q4 in this repository).",
    )
    parser.add_argument(
        "--tokenizer-output",
        type=pathlib.Path,
        default=DEFAULT_TOKENIZER_OUTPUT,
        help="Destination directory for tokenizer files (default: models/qwen3.5-9b-tokenizer in this repository).",
    )
    parser.add_argument(
        "--skip-model",
        action="store_true",
        help="Skip downloading the 5.68 GB GGUF model weights (tokenizer only).",
    )
    parser.add_argument(
        "--skip-tokenizer",
        action="store_true",
        help="Skip downloading tokenizer files.",
    )
    args = parser.parse_args()
    output = args.output.resolve()
    tokenizer_output = args.tokenizer_output.resolve()

    if not args.skip_tokenizer:
        try:
            download_tokenizer(tokenizer_output)
            print(f"Tokenizer ready at: {tokenizer_output}")
        except Exception as error:
            parser.exit(1, f"Tokenizer download failed: {error}\n")

    if not args.skip_model:
        model_file = output / MODEL_FILE
        try:
            if model_file.is_file():
                print(f"Checking existing model: {model_file}", flush=True)
                verify_model(model_file)
                print("Existing model verified; download skipped.")
            else:
                from huggingface_hub import hf_hub_download

                output.mkdir(parents=True, exist_ok=True)
                print(f"Downloading {REPO_ID}/{MODEL_FILE} (5.68 GB)...", flush=True)
                downloaded = pathlib.Path(
                    hf_hub_download(
                        repo_id=REPO_ID,
                        filename=MODEL_FILE,
                        revision=REVISION,
                        local_dir=str(output),
                    )
                )
                verify_model(downloaded)
            print(f"Model ready (size and SHA-256 verified): {model_file}")
        except (OSError, ValueError) as error:
            parser.exit(1, f"Model preparation failed: {error}\n")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
