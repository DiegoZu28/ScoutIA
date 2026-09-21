#!/usr/bin/env bash
# Baja todo lo que levantó scripts/compartir_app.sh: el túnel público y el backend en :8000.
# A partir de acá no se consume nada (ni cómputo local ni tokens de OpenAI, que de por sí
# solo se gastan cuando alguien usa el comparador con narrativa LLM).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "Deteniendo túnel de Cloudflare..."
if [ -f "$ROOT/logs/tunnel.pid" ]; then
  kill "$(cat "$ROOT/logs/tunnel.pid")" 2>/dev/null || true
  rm -f "$ROOT/logs/tunnel.pid"
fi
pkill -f "cloudflared tunnel --url http://localhost:8000" 2>/dev/null || true

echo "Deteniendo backend en el puerto 8000..."
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill 2>/dev/null || true

echo "Listo, la app está bajada."
