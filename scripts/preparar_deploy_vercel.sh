#!/usr/bin/env bash
# Copia los artefactos servibles (models/ + dataset.parquet + imagenes_jugadores.json) hacia
# app/models/ y app/data/processed/. Necesario porque el servicio de backend en Vercel
# (vercel.json, root: "app") solo empaqueta lo que vive DENTRO de app/ -- no ve los originales
# en la raíz del repo, que siguen sin versionarse (se regeneran con
# scripts/build_model_artifacts.py). Correr esto cada vez que el modelo se regenere y antes
# de cada deploy a Vercel.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p app/models app/data/processed
cp models/*.joblib models/metadata.json app/models/
cp data/processed/dataset.parquet data/processed/imagenes_jugadores.json app/data/processed/

echo "Copiado a app/models/ y app/data/processed/:"
du -sh app/models app/data/processed
echo ""
echo "Recordá: 'git add app/models app/data' + commit para que el próximo deploy en Vercel"
echo "sirva estos artefactos actualizados."
