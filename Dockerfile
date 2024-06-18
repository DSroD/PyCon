FROM python:3.12
LABEL authors="dsrod"

WORKDIR /app

COPY ./ /app

RUN pip install --no-cache-dir --upgrade -r /app/requirements.deployment.txt

EXPOSE 80

CMD ["python", "-u", "-m", "uvicorn", "main:app", "--port", "80", "--host", "0.0.0.0"]
