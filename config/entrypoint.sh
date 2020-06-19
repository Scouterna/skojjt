#!/usr/bin/env sh
set -e

. /uwsgi-nginx-entrypoint.sh
rm /etc/nginx/conf.d/default.conf
rm /etc/nginx/conf.d/nginx.conf

exec "$@"
