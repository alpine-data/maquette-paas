FROM alpine:3.16

RUN \
    apk add python3 nginx curl && \
    curl -sSL https://install.python-poetry.org | python3 -

ENV \
    PATH="$PATH:/root/.local/bin" \
    MQ_SERVER__NGINX__PID_FILE="/etc/nginx/nginx.pid" \
    MQ_SERVER__NGINX__CONFIG_FILE="/etc/nginx/nginx.conf"

EXPOSE 80

WORKDIR /opt/mq-apps

ADD ./pyproject.toml ./poetry.lock /opt/mq-apps
RUN poetry install --no-root

ADD . /opt/mq-apps/
RUN poetry install

CMD \
    poetry run mq server configure-nginx && \
    nginx && \
    poetry run mq server run