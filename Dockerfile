FROM python:3.10-slim

RUN addgroup --system app_group && adduser --system --ingroup app_group app_user

WORKDIR /app

COPY ./app.py ./requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

RUN apt-get update && apt-get install -y curl

RUN chown -R app_user:app_group /app

USER app_user

EXPOSE 5000

ENTRYPOINT ["python"]
CMD ["app.py"]