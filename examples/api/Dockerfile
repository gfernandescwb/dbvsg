FROM python:3.11-slim

WORKDIR /app

COPY database_versioning/dbvsg /app/dbvsg
COPY database_versioning/examples/api /app

RUN pip install --no-cache-dir -r requirements.txt

COPY database_versioning/examples/api/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app
ENV FLASK_APP=app.run:app
ENV PYTHONUNBUFFERED=1

CMD ["/entrypoint.sh"]
