#!/bin/sh
# Run by the visitor devcontainer's postAttachCommand, inside the `web` container, each time an editor attaches.
# It waits for the site to answer on port 8000 and prints its forwarded address. It runs no boot and changes nothing
# (req-rampart-20x-playground-codespaces-14).
echo 'Starting the 20x Playground. A new Codespace takes about eight minutes. This terminal prints the link when the site is ready.'
n=0
until curl -s -o /dev/null --max-time 3 http://127.0.0.1:8000/ || [ "$n" -ge 240 ]; do
    n=$((n + 1))
    sleep 5
done
echo
if [ "$n" -ge 240 ]; then
    echo 'The site did not start within 20 minutes. Please report it: https://github.com/unified-systems-com/rampart-20x-playground-tap/issues'
else
    echo "The 20x Playground is ready: https://$CODESPACE_NAME-8000.$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"
    echo 'Open that link, then sign in with the GitHub account that opened this Codespace.'
fi
