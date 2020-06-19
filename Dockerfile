FROM tiangolo/uwsgi-nginx-flask:python3.8-alpine
COPY config/supervisord.ini /etc/supervisor.d/supervisord.ini
COPY config/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY config/nginx.server.conf /etc/nginx/conf.d/narvaro.conf
COPY config/uwsgi.ini /etc/uwsgi.ini
COPY config/requirements.txt /tmp/
RUN pip install -U pip
RUN pip install -r /tmp/requirements.txt

COPY app /app
COPY build /static/build
COPY src/html /static/src/html
COPY src/img /static/src/img
COPY src/less /static/src/less
COPY src/ts /static/src/ts

ENV STATIC_INDEX=1 STATIC_PATH=/static/ UWSGI_INI=/etc/uwsgi.ini STATIC_URL=/static

WORKDIR /tmp