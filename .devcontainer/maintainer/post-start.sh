#!/usr/bin/env bash
# The visitor configuration runs this boot inside `web` (its service). The maintainer configuration's
# service is `devbox`, so the same second boot runs in `web` through the Docker socket: wait for the
# server, load the environment the entrypoint derived, run `manage.py boot` (it fires the collector the
# first boot could not).
set -euo pipefail
project=$(docker inspect "$(hostname)" --format '{{ index .Config.Labels "com.docker.compose.project" }}')
web=$(docker ps -q --filter "label=com.docker.compose.project=${project}" --filter "label=com.docker.compose.service=web" | head -1)
[ -n "$web" ] || { echo "post-start: no web container in project ${project}" >&2; exit 1; }
until [ "$(docker exec "$web" curl -s -o /dev/null -w '%{http_code}' -H 'Host: localhost' http://127.0.0.1:8000/healthz)" != 000 ]; do sleep 5; done
docker exec "$web" sh -c 'set -a; . /run/tap-codespace.env; set +a; uv run python manage.py boot'
