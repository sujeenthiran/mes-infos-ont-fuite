#!/usr/bin/env bash
# Mes infos ont fuité ? — lanceur Linux / macOS
cd "$(dirname "$0")" || exit 1
for py in python3 python; do
  if command -v "$py" >/dev/null 2>&1 && "$py" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)' 2>/dev/null; then
    exec "$py" mes_infos_ont_fuite.py "$@"
  fi
done
echo "Python 3.8+ est nécessaire."
if [ "$(uname)" = "Darwin" ]; then
  echo "Installe-le depuis https://www.python.org/downloads/ puis relance ce fichier."
  open "https://www.python.org/downloads/" 2>/dev/null
else
  echo "Installe-le avec :  sudo apt install python3   (Debian/Ubuntu)"
fi
read -r -p "Appuie sur Entrée pour fermer…" _
exit 1
