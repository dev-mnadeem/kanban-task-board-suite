# syntax=docker/dockerfile:1

# ---------- build ----------------------------------------------------------
# Wheels are built once here so the runtime image carries no compiler.
FROM python:3.12-slim AS build

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /wheels
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && python -m pip wheel --wheel-dir /wheels -r requirements.txt

# ---------- runtime --------------------------------------------------------
FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# curl is used by the healthcheck below.
RUN apt-get update \
 && apt-get install --no-install-recommends -y curl \
 && rm -rf /var/lib/apt/lists/*

# Never run the application as root.
RUN useradd --create-home --uid 10001 appuser

WORKDIR /app

COPY --from=build /wheels /wheels
COPY requirements.txt .
RUN python -m pip install --no-index --find-links=/wheels -r requirements.txt \
 && rm -rf /wheels

COPY --chown=appuser:appuser . .

USER appuser

EXPOSE 8001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD curl -fsS -X POST http://localhost:8001/graphql \
      -H 'Content-Type: application/json' \
      -d '{"query":"{ lanes { id } }"}' || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]
CMD ["python", "manage.py", "runserver", "0.0.0.0:8001"]
