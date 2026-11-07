"""Download only the local Qwen GGUF checkpoint and tokenizer assets."""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil


REPO_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct-GGUF"
TOKENIZER_REPO_ID = "Qwen/Qwen2.5-Coder-1.5B-Instruct"
MODEL_FILE = "qwen2.5-coder-1.5b-instruct-q4_k_m.gguf"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=pathlib.Path, default=pathlib.Path("models/qwen2.5-coder-1.5b-q4"))
    args = parser.parse_args()
    from huggingface_hub import snapshot_download

    model_patterns = [MODEL_FILE, "LICENSE*", "README.md"]
    tokenizer_patterns = [
        "config.json",
        "generation_config.json",
        "tokenizer.json",
        "tokenizer_config.json",
        "special_tokens_map.json",
        "vocab.json",
        "merges.txt",
        "added_tokens.json",
    ]
    args.output.mkdir(parents=True, exist_ok=True)
    downloaded = pathlib.Path(snapshot_download(
        repo_id=REPO_ID,
        local_dir=str(args.output.resolve()),
        allow_patterns=model_patterns,
    ))
    snapshot_download(
        repo_id=TOKENIZER_REPO_ID,
        local_dir=str(args.output.resolve()),
        allow_patterns=tokenizer_patterns,
    )
    model_file = downloaded / MODEL_FILE
    if not model_file.is_file():
        raise FileNotFoundError(f"Expected GGUF file was not downloaded: {model_file}")
    # This GGUF stores an output.weight matrix; mistral.rs requires an untied-head config
    # even though the upstream Transformers config describes tied embeddings.
    runtime_dir = args.output.resolve() / "mistralrs_runtime"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    for filename in tokenizer_patterns:
        source = args.output.resolve() / filename
        if source.is_file():
            shutil.copy2(source, runtime_dir / filename)
    config_path = runtime_dir / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["tie_word_embeddings"] = False
    config_path.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8")
    print(f"Model ready: {model_file}")
    print("Run with: $env:DATAMATE_MODEL_PATH = \"" + str(model_file) + "\"")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
