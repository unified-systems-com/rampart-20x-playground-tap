#!/bin/sh
# Run by postStartCommand on every start: in `web` for a visitor, in `devbox` for a maintainer. It copies the three
# identity keys tap's entrypoint needs out of Codespaces' own shared env file into the file `web` reads at
# TAP_CODESPACE_IDENTITY (tap v0.4.5, req-tap-serving-codespace-9). A prebuilt Codespace's containers were created
# during the prebuild, when the Codespace had no name, and are only restarted on resume, so the name has to arrive by
# file (req-rampart-20x-playground-codespaces-15). It copies ONLY those three keys: the shared file also holds
# GITHUB_TOKEN and GITHUB_CODESPACE_TOKEN.
set -eu
dst="$1"
src=/workspaces/.codespaces/shared/.env
_key() { sed -n "s/^$1=[\"']\{0,1\}\([^\"']*\)[\"']\{0,1\}\$/\1/p" "$src" 2>/dev/null | tail -1; }
# Codespaces writes the shared file a few seconds after the containers start (measured 2026-11-22: 3 s), so wait for it.
i=0
while [ -z "$(_key CODESPACE_NAME)" ] && [ "$i" -lt 120 ]; do
    sleep 1
    i=$((i + 1))
done
if [ -z "$(_key CODESPACE_NAME)" ]; then
    echo "codespace-identity: no CODESPACE_NAME in $src after 120 s; the site will not start" >&2
    exit 1
fi
# One printf, written in place: a truncate keeps the inode the bind mount follows, and the reader takes the file only
# when one read of it holds all three keys.
printf 'CODESPACE_NAME=%s\nGITHUB_CODESPACES_PORT_FORWARDING_DOMAIN=%s\nGITHUB_USER=%s\n' \
    "$(_key CODESPACE_NAME)" "$(_key GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN)" "$(_key GITHUB_USER)" > "$dst"
