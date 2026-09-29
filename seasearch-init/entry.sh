#!/bin/bash
# Runs the image's own entrypoint, but starts Seafile through our start.py
# wrapper so seafevents.conf is configured for SeaSearch before seafevents runs.
set -e

sed 's#^\( *\)/scripts/start.py &#\1python3 /scripts-seasearch/start.py \&#' \
    /scripts/enterpoint.sh > /tmp/enterpoint.sh

if ! grep -q '/scripts-seasearch/start.py' /tmp/enterpoint.sh; then
    echo "seasearch-init: could not find '/scripts/start.py &' in /scripts/enterpoint.sh; the image layout changed." >&2
    exit 1
fi

exec bash /tmp/enterpoint.sh
