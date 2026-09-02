"""Descarga plantillas de Transfermarkt para las 5 grandes ligas.

Fase 1: obtiene los IDs de club por liga y temporada.
Fase 2: descarga el HTML crudo de cada plantilla club-temporada.

El parseo NO se hace aquí: se guarda el HTML crudo para poder
reprocesarlo sin volver a scrapear.

Uso:
    python scripts/descargar_transfermarkt.py
"""
from pathlib import Path
import csv
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/transfermarkt"
HTML = RAW / "plantillas_html"
HTML.mkdir(parents=True, exist_ok=True)

CLUBES_CSV = RAW / "clubes.csv"

LIGAS = {
    "GB1": "Premier League",
    "ES1": "La Liga",
    "IT1": "Serie A",
    "L1": "Bundesliga",
    "FR1": "Ligue 1",
}

# saison_id es el año de inicio: 2021 -> temporada 2021-2022
TEMPORADAS = [2021, 2022, 2023, 2024, 2025]

BASE = "https://www.transfermarkt.com"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
}

ESPERA = 3          # segundos entre requests
REINTENTOS = 3


def pedir(url):
    """GET con reintentos y espera. Devuelve el texto o None."""
    for intento in range(1, REINTENTOS + 1):
        try:
            r = requests.get(url, headers=HEADERS, timeout=30)
            if r.status_code == 200:
                return r.text
            print(f"    status {r.status_code} (intento {intento})", flush=True)
        except Exception as e:
            print(f"    error {e!r} (intento {intento})", flush=True)
        time.sleep(ESPERA * intento)
    return None


# ---------------------------------------------------------------- fase 1

def obtener_clubes():
    """Devuelve lista de dicts con liga, temporada, club_id y nombre."""
    filas = []
    for codigo, nombre_liga in LIGAS.items():
        for anio in TEMPORADAS:
            url = (f"{BASE}/-/startseite/wettbewerb/{codigo}"
                   f"/plus/?saison_id={anio}")
            print(f"[liga] {nombre_liga} {anio}", flush=True)

            html = pedir(url)
            if html is None:
                print("    SIN RESPUESTA", flush=True)
                continue

            soup = BeautifulSoup(html, "lxml")
            vistos = set()
            for a in soup.select("table.items a[href*='/startseite/verein/']"):
                m = re.search(r"/startseite/verein/(\d+)", a["href"])
                if not m:
                    continue
                club_id = m.group(1)
                if club_id in vistos:
                    continue
                vistos.add(club_id)
                filas.append({
                    "liga_codigo": codigo,
                    "liga": nombre_liga,
                    "saison_id": anio,
                    "club_id": club_id,
                    "club": a.get_text(strip=True) or a.get("title", ""),
                })

            print(f"    {len(vistos)} clubes", flush=True)
            time.sleep(ESPERA)

    return filas


# ---------------------------------------------------------------- fase 2

def descargar_plantillas(clubes):
    """Guarda el HTML crudo de cada plantilla club-temporada."""
    total = len(clubes)
    for n, c in enumerate(clubes, start=1):
        destino = HTML / f"{c['liga_codigo']}_{c['saison_id']}_{c['club_id']}.html"
        if destino.exists():
            print(f"[{n}/{total}] SALTADO {destino.name}", flush=True)
            continue

        url = (f"{BASE}/-/kader/verein/{c['club_id']}"
               f"/saison_id/{c['saison_id']}/plus/1")
        html = pedir(url)

        if html is None:
            print(f"[{n}/{total}] FALLO {destino.name}", flush=True)
            continue

        # Verificación mínima antes de guardar
        if "table.items" not in html and 'class="items"' not in html:
            print(f"[{n}/{total}] SIN TABLA {destino.name}", flush=True)

        destino.write_text(html, encoding="utf-8")
        print(f"[{n}/{total}] OK {destino.name} ({len(html)} bytes)", flush=True)
        time.sleep(ESPERA)


# ---------------------------------------------------------------- main

def main():
    if CLUBES_CSV.exists():
        print(f"Usando {CLUBES_CSV.name} existente.", flush=True)
        with CLUBES_CSV.open(encoding="utf-8") as f:
            clubes = list(csv.DictReader(f))
    else:
        print("=== Fase 1: obteniendo clubes ===", flush=True)
        clubes = obtener_clubes()
        if not clubes:
            print("No se obtuvo ningún club. Revisa el selector.", flush=True)
            sys.exit(1)
        with CLUBES_CSV.open("w", newline="", encoding="utf-8") as f:
            w = csv.DictWriter(f, fieldnames=list(clubes[0].keys()))
            w.writeheader()
            w.writerows(clubes)
        print(f"Guardados {len(clubes)} registros en {CLUBES_CSV.name}", flush=True)

    print(f"\n=== Fase 2: descargando {len(clubes)} plantillas ===", flush=True)
    descargar_plantillas(clubes)
    print("\nTerminado.", flush=True)


if __name__ == "__main__":
    main()