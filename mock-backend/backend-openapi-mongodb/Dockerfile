###########
# BUILDER #
###########

# pull official base image
FROM jquinno/alpine-pandas  as builder

# set work directory
WORKDIR /usr/src/app

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

RUN apk update && apk -U upgrade && \
    apk add --no-cache --virtual .build-deps \
        postgresql-dev \
        openssl-dev \
        libffi-dev \
        cargo \
        linux-headers 

# lint
RUN pip install --upgrade pip


# install python dependencies
COPY ./requirements.txt .
RUN pip wheel --no-cache-dir --wheel-dir /usr/src/app/wheels -r requirements.txt


#########
# FINAL #
#########

# pull official base image
FROM jquinno/alpine-pandas

# create directory for the app user
RUN mkdir -p /home/app

# create the app user
#RUN addgroup --system app && adduser --system --group app
RUN addgroup -S appgroup && adduser -S appuser -G appgroup

# create the appropriate directories
ENV HOME=/home/app
ENV APP_HOME=/home/app/web
RUN mkdir $APP_HOME
WORKDIR $APP_HOME

# install dependencies
RUN apk update && apk add --no-cache netcat-openbsd libpq

COPY --from=builder /usr/src/app/wheels /wheels
COPY --from=builder /usr/src/app/requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache /wheels/*

# copy project
COPY . $APP_HOME

# chown all the files to the app user
RUN chown -R appuser:appgroup $APP_HOME

# change to the app user
USER appuser

CMD ["gunicorn","--bind","0.0.0.0:9090","wsgi:app"]
