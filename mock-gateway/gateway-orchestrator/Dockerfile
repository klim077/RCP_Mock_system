FROM python:latest

ARG HOST_DOCKER_INTERNAL
# ARG LOCAL_PYPI_PORT

WORKDIR /app

COPY . .

RUN pip install -r requirements.txt

CMD ["python", "-u", "app2.py"]

ENTRYPOINT [ "./entrypoint.sh" ]
