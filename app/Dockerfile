FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1
ENV PIP_ROOT_USER_ACTION=ignore

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
