FROM python:3.10

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

ENTRYPOINT celery -A rower_saving_worker worker --autoscale 10 --loglevel=info -n rowerSavingWorker -Q rower_saving_queue
