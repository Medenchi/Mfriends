#!/usr/bin/env bash
set -euo pipefail

LOG_FILE="/opt/mfriends/logs/duckdns.log"
mkdir -p "$(dirname "$LOG_FILE")"

if [[ -z "${DUCKDNS_DOMAIN:-}" || -z "${DUCKDNS_TOKEN:-}" ]]; then
  echo "$(date -Is) missing DUCKDNS_DOMAIN or DUCKDNS_TOKEN" >> "$LOG_FILE"
  exit 1
fi

for attempt in 1 2 3 4 5; do
  RESPONSE="$(curl -fsS --retry 2 --connect-timeout 8 "https://www.duckdns.org/update?domains=${DUCKDNS_DOMAIN}&token=${DUCKDNS_TOKEN}&ip=" || true)"
  if [[ "$RESPONSE" == "OK" ]]; then
    echo "$(date -Is) duckdns update OK" >> "$LOG_FILE"
    exit 0
  fi
  echo "$(date -Is) duckdns attempt ${attempt} failed: ${RESPONSE:-network-error}" >> "$LOG_FILE"
  sleep $((attempt * 5))
done

exit 1
