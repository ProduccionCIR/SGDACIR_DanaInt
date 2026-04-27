#!/usr/bin/env bash
# Arranque en Codespaces / Linux sin depender del comando `streamlit` en el PATH.
set -euo pipefail
cd "$(dirname "$0")"
python3 -m pip install -q -r requirements.txt
exec python3 -m streamlit run app.py
