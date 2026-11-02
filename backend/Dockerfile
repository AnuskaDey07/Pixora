# syntax=docker/dockerfile:1.7

# ─────────────────────────────────────────────────────────────
# Stage 1: build wheels (base + optional ML variant)
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        build-essential libpq-dev libjpeg-dev zlib1g-dev libwebp-dev

WORKDIR /wheels
COPY requirements.txt .

ARG INSTALL_ML=0
ARG ML_VARIANT=cpu
COPY app/ml/requirements-ml.txt /tmp/req-cpu.txt
COPY app/ml/requirements-ml-cuda.txt /tmp/req-cuda.txt

RUN --mount=type=cache,target=/root/.cache/pip \
    pip wheel --wheel-dir=/wheels -r requirements.txt && \
    if [ "$INSTALL_ML" = "1" ]; then \
      if [ "$ML_VARIANT" = "cuda" ]; then \
        pip wheel --wheel-dir=/wheels -r /tmp/req-cuda.txt; \
      else \
        pip wheel --wheel-dir=/wheels -r /tmp/req-cpu.txt; \
      fi; \
    fi && rm -f /tmp/req-cpu.txt /tmp/req-cuda.txt


# ─────────────────────────────────────────────────────────────
# Stage 2: runtime
# ─────────────────────────────────────────────────────────────
FROM python:3.12-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONPATH=/app

RUN --mount=type=cache,target=/var/cache/apt,sharing=locked \
    --mount=type=cache,target=/var/lib/apt,sharing=locked \
    apt-get update && apt-get install -y --no-install-recommends \
        libpq5 libjpeg62-turbo zlib1g libwebp7 curl postgresql-client \
        libgl1 libglib2.0-0 libxcb1 libxrender1 libsm6 libxext6

RUN groupadd --gid 1000 appuser \
 && useradd  --uid 1000 --gid 1000 --create-home --shell /bin/bash appuser

WORKDIR /app

COPY --from=builder /wheels /wheels
COPY requirements.txt .
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

ARG INSTALL_ML=0
ARG ML_VARIANT=cpu
COPY app/ml/requirements-ml.txt /tmp/req-cpu.txt
COPY app/ml/requirements-ml-cuda.txt /tmp/req-cuda.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    if [ "$INSTALL_ML" = "1" ]; then \
      if [ "$ML_VARIANT" = "cuda" ]; then \
        pip install -r /tmp/req-cuda.txt; \
      else \
        pip install -r /tmp/req-cpu.txt; \
      fi; \
    fi && rm -f /tmp/req-cpu.txt /tmp/req-cuda.txt

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-k", "gthread", "--threads", "4", "-b", "0.0.0.0:5000", "--access-logfile", "-", "--error-logfile", "-", "app:create_app()"]
