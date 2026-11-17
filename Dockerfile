FROM vllm/vllm-openai:v0.33.0

ENTRYPOINT []

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PIP_NO_CACHE_DIR=1 \
    NCCL_P2P_DISABLE=1 \
    PYTHONUNBUFFERED=1 \
    DATAMATE_MODEL_PATH=/models/qwen3.5-9b-q4/Qwen3.5-9B-Q4_K_M.gguf \
    DATAMATE_TOKENIZER_PATH=/models/qwen3.5-9b-tokenizer \
    DATAMATE_CONTEXT_SIZE=4096

WORKDIR /code

RUN mkdir -p /models /data /result /result/logs

# Install locked dependencies via uv
COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/
RUN uv sync --locked --no-dev --no-install-project

# Copy offline model weights and tokenizer (cached layer)
COPY models/ /models/

# Copy training documentation / manifest (BTC Rule 8)
COPY training_code/ /code/training_code/

# Copy inference runtime and entrypoint
COPY predict.sh README.md requirements.txt /code/
COPY src/ /code/src/
RUN uv sync --locked --no-dev
RUN chmod +x /code/predict.sh

CMD ["bash", "/code/predict.sh"]
