#!/bin/sh
# Run by the visitor devcontainer's postAttachCommand, inside the `web` container, each time an editor attaches.
# It waits for the site to answer on port 8000 and prints its forwarded address. It runs no boot and changes nothing
# (req-rampart-20x-playground-codespaces-14).
echo 'Starting the 20x Playground. A new Codespace takes about eight minutes. This terminal prints the link when the site is ready.'
# Ready means the site answers without an error status (--fail): it answers a signed-out request with a redirect to the
# sign-in page, and binds port 8000 only after the boot has finished. The limit is a wall-clock deadline, so stalled
# requests cannot stretch it.
deadline=$(($(date +%s) + 1200))
ready=0
while [ "$(date +%s)" -lt "$deadline" ]; do
    if curl -s -f -o /dev/null --max-time 3 http://127.0.0.1:8000/; then
        ready=1
        break
    fi
    sleep 5
done
echo
if [ "$ready" -eq 1 ]; then
    echo "The 20x Playground is ready: https://$CODESPACE_NAME-8000.$GITHUB_CODESPACES_PORT_FORWARDING_DOMAIN"
    echo 'Open that link, then sign in with the GitHub account that opened this Codespace.'
else
    echo 'The site did not start within 20 minutes. Please report it: https://github.com/unified-systems-com/rampart-20x-playground-tap/issues'
fi
