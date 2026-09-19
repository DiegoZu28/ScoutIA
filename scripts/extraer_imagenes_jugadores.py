"""Extrae foto, bandera de nacionalidad y escudo de club desde las plantillas de
Transfermarkt ya descargadas (data/raw/transfermarkt/plantillas_html).

No hace ningún request nuevo: reusa el HTML crudo que ya bajó
descargar_transfermarkt.py. Solo procesa las plantillas de la temporada más
reciente (2025-2026) y filtra a los player_id que efectivamente están vigentes
en el dataset procesado, que es exactamente el universo de jugadores que la
app permite buscar (ver DatasetRepository).

El escudo se resuelve por club (todos los jugadores de una misma plantilla
comparten el mismo escudo), usando el club_id embebido en el nombre del
archivo -- así no hace falta cruzar por nombre de equipo (fuente de bugs de
merge ya vistos entre FBref y Transfermarkt). La bandera se resuelve por
jugador, tomando la primera bandera de la fila de la tabla que contiene su
enlace de perfil.

Uso:
    python scripts/extraer_imagenes_jugadores.py
"""
from pathlib import Path
import json
import re

from bs4 import BeautifulSoup
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PLANTILLAS = ROOT / "data/raw/transfermarkt/plantillas_html"
DATASET = ROOT / "data/processed/dataset.parquet"
DESTINO = ROOT / "data/processed/imagenes_jugadores.json"

TEMPORADA = 2025  # saison_id de la temporada 2025-2026 (la más reciente del dataset)


def jugadores_vigentes() -> set[str]:
    df = pd.read_parquet(DATASET)
    return set(df.loc[df["saison_id"] == df["saison_id"].max(), "player_id"].astype(str))


def _club_id_de(archivo: Path) -> str:
    # nombre de archivo: {liga_codigo}_{saison_id}_{club_id}.html
    return archivo.stem.split("_")[-1]


def _escudo_del_club(soup: BeautifulSoup, club_id: str) -> str | None:
    crest = soup.select_one(f'img[src*="/wappen/"][src*="/{club_id}."]')
    if crest is None:
        crest = soup.select_one(f'img[src*="/wappen/"][src*="/{club_id}_"]')
    return crest["src"] if crest is not None else None


def extraer_de_plantilla(html: str, club_id: str) -> dict[str, dict[str, str | None]]:
    soup = BeautifulSoup(html, "lxml")
    escudo_url = _escudo_del_club(soup, club_id)

    imagenes: dict[str, dict[str, str | None]] = {}
    for bloque in soup.select("table.inline-table"):
        foto = bloque.select_one("img[data-src*='/portrait/']")
        link = bloque.select_one("a[href*='/profil/spieler/']")
        if foto is None or link is None:
            continue
        m = re.search(r"/profil/spieler/(\d+)", link["href"])
        if not m:
            continue
        pid = m.group(1)

        fila = bloque.find_parent("tr")
        bandera = fila.select_one("img.flaggenrahmen") if fila is not None else None

        imagenes[pid] = {
            "foto_url": foto["data-src"],
            "bandera_url": bandera["src"] if bandera is not None else None,
            "escudo_url": escudo_url,
        }
    return imagenes


def main():
    vigentes = jugadores_vigentes()
    plantillas = sorted(PLANTILLAS.glob(f"*_{TEMPORADA}_*.html"))
    print(f"{len(plantillas)} plantillas de la temporada {TEMPORADA}-{TEMPORADA + 1}")

    imagenes: dict[str, dict[str, str | None]] = {}
    for archivo in plantillas:
        html = archivo.read_text(encoding="utf-8", errors="ignore")
        imagenes.update(extraer_de_plantilla(html, _club_id_de(archivo)))

    imagenes_vigentes = {pid: datos for pid, datos in imagenes.items() if pid in vigentes}

    con_foto = sum(1 for d in imagenes_vigentes.values() if d["foto_url"])
    con_bandera = sum(1 for d in imagenes_vigentes.values() if d["bandera_url"])
    con_escudo = sum(1 for d in imagenes_vigentes.values() if d["escudo_url"])
    print(f"{len(imagenes_vigentes)}/{len(vigentes)} jugadores vigentes con datos encontrados")
    print(f"  con foto: {con_foto}, con bandera: {con_bandera}, con escudo: {con_escudo}")

    DESTINO.write_text(json.dumps(imagenes_vigentes, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Guardado en {DESTINO}")


if __name__ == "__main__":
    main()
