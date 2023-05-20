FROM python:3.11.3-slim-buster

RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt /app/
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY . /app
COPY ./google_creeds.json .
WORKDIR /app
CMD ["python", "main.py"]