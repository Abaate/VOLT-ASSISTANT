#!/usr/bin/env bash
set -euo pipefail
rm -f VOLT-Assistant.zip
zip -r VOLT-Assistant.zip . -x '.git/*' '.venv/*' '__pycache__/*' '*.pyc' '*.db' 'logs/*' 'android/**/.gradle/*'
