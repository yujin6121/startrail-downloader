#!/usr/bin/env bash
# Run the downloader with default input file.
if [ -f .env ]; then
  set -a
  . ./.env
  set +a
fi

if [ -z "${STARTRAIL_COOKIE:-}" ] || [[ "$STARTRAIL_COOKIE" == *"..."* ]]; then
  echo "[INFO] Protected artwork may need browser cookies."
  echo "[INFO] Put STARTRAIL_COOKIE='startrail_sid=...; startrail_progress=...' in .env"
fi
python3 download_images.py download.txt
