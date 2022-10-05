FROM python:3.7

ARG HOST_DOCKER_INTERNAL
# ARG LOCAL_PYPI_PORT

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY ./ .

COPY ./common .

CMD ["python", "-u", "control2.py"]
