FROM python:3.7

ARG HOST_DOCKER_INTERNAL
# ARG LOCAL_PYPI_PORT

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD celery -A gateway_controller_worker worker --autoscale 10 --loglevel="INFO"

ENTRYPOINT [ "./entrypoint.sh" ]
