FROM python:3.9-slim

WORKDIR /app
COPY poller.py /app/poller.py

RUN pip install requests

CMD ["python", "/app/poller.py"]

