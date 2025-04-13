FROM python:3.11-slim

WORKDIR /app

COPY dbvsg /app/dbvsg
COPY examples /app

RUN pip install --no-cache-dir -r requirements.txt

COPY examples/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENV PYTHONPATH=/app
ENV FLASK_APP=app.run:app
ENV PYTHONUNBUFFERED=1

CMD ["/entrypoint.sh"]
