FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ARG MISTRALRS_CUDA_WHEEL_URL=
ARG DATAMATE_MEMORY_GOAL=none

ENV UV_PROJECT_ENVIRONMENT=/opt/venv \
    PATH="/opt/venv/bin:$PATH" \
    DATAMATE_MODEL_PATH=/models/qwen2.5-coder-1.5b-q4/qwen2.5-coder-1.5b-instruct-q4_k_m.gguf \
    DATAMATE_RERANKER_PATH=/artifacts/reranker.joblib \
    DATAMATE_POLICY_PATH=/artifacts/policy.joblib \
    DATAMATE_CONTEXT_SIZE=3072

WORKDIR /code
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-dev
RUN if [ -n "$MISTRALRS_CUDA_WHEEL_URL" ]; then \
      uv pip install --python /opt/venv/bin/python --no-deps "$MISTRALRS_CUDA_WHEEL_URL"; \
    fi
ENV DATAMATE_MEMORY_GOAL=${DATAMATE_MEMORY_GOAL}

COPY src/ /code/src/
COPY predict.sh /code/predict.sh
COPY models/qwen2.5-coder-1.5b-q4/ /models/qwen2.5-coder-1.5b-q4/
COPY artifacts/ /artifacts/
RUN chmod +x /code/predict.sh

ENTRYPOINT ["/code/predict.sh"]
