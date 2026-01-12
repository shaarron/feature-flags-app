# STAGE 1: Builder
FROM python:3.10-slim AS builder

WORKDIR /app

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


# STAGE 2: Final Runtime
FROM python:3.10-slim

RUN addgroup --gid 1001 app_group && \
    adduser --uid 1001 \
            --gid 1001 \
            --disabled-password \
            --no-create-home \
            app_user

WORKDIR /app

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY --chown=1001:1001 api/ api/
ENV PYTHONPATH="${PYTHONPATH}:/app/api"

USER app_user
EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["api/app.py"]