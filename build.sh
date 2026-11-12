#!/usr/bin/env bash
# Genera dist/Comparador-Linac (Linux/macOS). Requiere Python 3.10+.
set -euo pipefail
python3 -m venv .venv && source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
python tests/run_tests.py
pyinstaller --noconfirm comparador.spec
cp -R ejemplos dist/ejemplos && cp README.md dist/README.md
echo "Listo: dist/Comparador-Linac"
