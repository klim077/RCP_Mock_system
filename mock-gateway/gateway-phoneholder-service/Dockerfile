FROM python:3.7

ARG HOST_DOCKER_INTERNAL
# ARG LOCAL_PYPI_PORT

WORKDIR /app

COPY ./requirements.txt .

RUN pip install -r requirements.txt

COPY . .

CMD [ "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "16000" ]

ENTRYPOINT [ "./entrypoint.sh" ]
