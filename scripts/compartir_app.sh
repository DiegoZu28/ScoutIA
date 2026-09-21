#!/usr/bin/env bash
# Compila el frontend, levanta backend+frontend juntos en un solo puerto (FastAPI sirve el
# build de Angular) y abre un túnel público de Cloudflare para que se pueda probar la app
# desde otro dispositivo/red (amigos, profe, etc.) sin desplegar nada.
#
# Para bajarla (y dejar de gastar cualquier costo asociado): scripts/detener_app.sh
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
mkdir -p logs

export NVM_DIR="$HOME/.nvm"
# shellcheck disable=SC1091
. "$NVM_DIR/nvm.sh"

echo "Compilando frontend..."
(cd frontend && npm run build)

echo "Liberando el puerto 8000 y cualquier túnel anterior..."
lsof -ti:8000 -sTCP:LISTEN | xargs -r kill 2>/dev/null || true
pkill -f "cloudflared tunnel --url http://localhost:8000" 2>/dev/null || true
sleep 1

echo "Iniciando backend en 0.0.0.0:8000..."
(cd app && nohup uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 > "$ROOT/logs/app_compartida.log" 2>&1 &)

echo "Esperando a que el backend responda..."
for _ in $(seq 1 30); do
  curl -sf "http://localhost:8000/openapi.json" >/dev/null 2>&1 && break
  sleep 1
done

echo "Abriendo túnel público (Cloudflare)..."
nohup cloudflared tunnel --url http://localhost:8000 > "$ROOT/logs/tunnel.log" 2>&1 &
echo $! > "$ROOT/logs/tunnel.pid"

echo "Esperando la URL pública..."
URL=""
for _ in $(seq 1 30); do
  URL=$(grep -oE 'https://[a-zA-Z0-9-]+\.trycloudflare\.com' "$ROOT/logs/tunnel.log" | tail -1 || true)
  [ -n "$URL" ] && break
  sleep 1
done

echo ""
if [ -n "$URL" ]; then
  echo "App pública en: $URL"
else
  echo "Todavía no aparece la URL del túnel — revisá logs/tunnel.log en unos segundos."
fi
echo "También accesible en tu red local: http://$(hostname -I | awk '{print $1}'):8000"
echo ""
echo "Para bajar todo: scripts/detener_app.sh"
