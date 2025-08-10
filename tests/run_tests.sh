#!/bin/bash

echo "🧪 Avvio test suite per Invoice App... NON FUNZIONANTE"

# Crea e attiva il virtualenv test
if [ ! -d ".venv_test" ]; then
  echo "📦 Creo virtualenv per test..."
  python3 -m venv .venv_test
fi
source .venv_test/bin/activate

echo "📦 Installazione dipendenze test..."
pip install -r tests/requirements_test.txt

echo "🔧 Setup ambiente test..."

echo "🚀 Esecuzione test unitari..."
export PYTHONPATH=$(pwd)
pytest tests/

echo "✅ Test completati!"

# opzionale: pulisci l'ambiente di test
deactivate
rm -rf .venv_test
