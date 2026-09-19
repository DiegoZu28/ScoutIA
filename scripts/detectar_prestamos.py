"""Detecta pares de cesión (club dueño <-> club donde juega cedido) a partir de las
insignias de transferencia en las plantillas de Transfermarkt ya descargadas.

Por qué hace falta: en 03-ingenieria_variables.ipynb (sección 2.1), cuando un jugador
aparece con más de un `Squad` en FBref la misma temporada, se resuelve quedándose con la
fila cuyo `Squad` coincide con el `club` de Transfermarkt (`club_coincide`). Esa regla
arregla bien el bug real que la motivó (dos jugadores *distintos* fusionados por
coincidencia de nombre en el cruce), pero para un jugador cedido el club de Transfermarkt
es el dueño de la ficha, no donde jugó -- así que la regla descarta sistemáticamente la
fila de la cesión (a veces toda su temporada) y deja la fila del club dueño, casi vacía.
Caso encontrado por el usuario: Endrick, cedido en Olympique Lyon toda 2025-2026 (16
partidos, 5 goles), Real Madrid solo le registra 12 minutos post-regreso -- pero
club_coincide se queda con la fila de Real Madrid.

Esta tabla identifica esos pares con evidencia EXPLÍCITA de Transfermarkt (insignias
"On loan from X until..." / "Returned after loan spell with X..."), para no adivinar por
minutos jugados -- adivinar arriesgaría reintroducir el bug de colisión de nombres que
club_coincide sí resuelve bien en los demás casos.

Uso:
    python scripts/detectar_prestamos.py
"""
from pathlib import Path
import csv
import re

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parent.parent
PLANTILLAS = ROOT / "data/raw/transfermarkt/plantillas_html"
DESTINO = ROOT / "data/interim/prestamos.csv"

RE_ON_LOAN = re.compile(r"^On loan from (.+) until")
RE_RETURNED = re.compile(r"^Returned after loan spell with (.+?);")


def _club_de_la_pagina(soup: BeautifulSoup, club_id: str) -> str | None:
    crest = soup.select_one(f'img[src*="/wappen/"][src*="/{club_id}."]')
    if crest is None:
        crest = soup.select_one(f'img[src*="/wappen/"][src*="/{club_id}_"]')
    return crest["title"] if crest is not None else None


def extraer_de_plantilla(html: str, club_id: str, saison_id: int) -> list[dict]:
    soup = BeautifulSoup(html, "lxml")
    club_pagina = _club_de_la_pagina(soup, club_id)
    if club_pagina is None:
        return []

    filas: list[dict] = []
    for bloque in soup.select("table.inline-table"):
        link = bloque.select_one("a[href*='/profil/spieler/']")
        if link is None:
            continue
        m = re.search(r"/profil/spieler/(\d+)", link["href"])
        if not m:
            continue
        pid = m.group(1)

        fila = bloque.find_parent("tr")
        badge = fila.select_one("span.wechsel-kader-wappen a[title]") if fila is not None else None
        if badge is None:
            continue
        titulo = badge["title"]

        m_on_loan = RE_ON_LOAN.match(titulo)
        m_returned = RE_RETURNED.match(titulo)
        if m_on_loan:
            # esta página es el club receptor (donde juega cedido); el dueño va en la insignia.
            filas.append({
                "player_id": pid,
                "saison_id": saison_id,
                "club_prestamo": club_pagina,
                "club_dueno": m_on_loan.group(1),
            })
        elif m_returned:
            # esta página es el club dueño; el club de la cesión va en la insignia.
            filas.append({
                "player_id": pid,
                "saison_id": saison_id,
                "club_prestamo": m_returned.group(1),
                "club_dueno": club_pagina,
            })
    return filas


def main():
    plantillas = sorted(PLANTILLAS.glob("*.html"))
    print(f"{len(plantillas)} plantillas")

    filas: list[dict] = []
    for archivo in plantillas:
        liga_codigo, saison_id, club_id = archivo.stem.split("_")
        html = archivo.read_text(encoding="utf-8", errors="ignore")
        filas.extend(extraer_de_plantilla(html, club_id, int(saison_id)))

    print(f"{len(filas)} insignias de cesión detectadas (antes de deduplicar)")

    # Un mismo par jugador-temporada puede detectarse desde las dos páginas (la del
    # club dueño Y la del club receptor) -- se queda con una sola fila por par.
    vistos: dict[tuple[str, int], dict] = {}
    for f in filas:
        vistos[(f["player_id"], f["saison_id"])] = f
    filas_unicas = list(vistos.values())
    print(f"{len(filas_unicas)} pares únicos (player_id, saison_id)")

    DESTINO.parent.mkdir(parents=True, exist_ok=True)
    with DESTINO.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["player_id", "saison_id", "club_prestamo", "club_dueno"])
        w.writeheader()
        w.writerows(filas_unicas)
    print(f"Guardado en {DESTINO}")


if __name__ == "__main__":
    main()
