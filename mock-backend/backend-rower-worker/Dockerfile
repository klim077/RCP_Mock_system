FROM python:3.7

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT celery -A rower_worker worker --autoscale 10 --loglevel=info -n rowerWorker -Q rower_queue
