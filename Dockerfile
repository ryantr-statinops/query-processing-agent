FROM vllm/vllm-openai:v0.10.1.1

ENTRYPOINT []

ENV HF_HUB_OFFLINE=1 \
    TRANSFORMERS_OFFLINE=1 \
    PIP_NO_CACHE_DIR=1 \
    NCCL_P2P_DISABLE=1 \
    PYTHONUNBUFFERED=1 \
    DATAMATE_MODEL_PATH=/models/qwen3.5-9b-q4/Qwen3.5-9B-Q4_K_M.gguf \
    DATAMATE_CONTEXT_SIZE=3072

WORKDIR /code

COPY pyproject.toml uv.lock ./
COPY --from=ghcr.io/astral-sh/uv:0.13.8 /uv /uvx /bin/
RUN uv sync --locked --no-dev

COPY predict.sh README.md /code/
COPY src/ /code/src/
COPY models/ /models/
RUN chmod +x /code/predict.sh

CMD ["bash", "/code/predict.sh"]
