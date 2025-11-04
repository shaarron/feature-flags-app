FROM python:3.10-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/* && \
    addgroup --system app_group && \
    adduser --system --ingroup app_group app_user

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

RUN chown -R app_user:app_group /app

USER app_user

EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["app.py"]