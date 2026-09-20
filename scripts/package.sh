#!/usr/bin/env bash
set -euo pipefail
./scripts/test.sh
rm -f VOLT-Assistant.zip VOLT-Assistant.sha256
zip -r VOLT-Assistant.zip . -x '.git/*' '.venv/*' '__pycache__/*' '*.pyc' '*.db' 'logs/*' '.env' 'android/**/.gradle/*' 'android/**/build/*'
sha256sum VOLT-Assistant.zip > VOLT-Assistant.sha256
