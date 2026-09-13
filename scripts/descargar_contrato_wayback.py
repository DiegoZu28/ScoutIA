"""Descarga vencimientos de contrato desde snapshots archivados (Wayback Machine)
de Transfermarkt, para las temporadas 2024-2025 y 2025-2026 -- las que no cubre
el dataset de Kaggle (que llega hasta FC24 / temporada 2023-2024).

Fase 1: por cada jugador que necesitamos, consulta el CDX de Wayback para
listar los snapshots disponibles de su ficha de Transfermarkt entre 2024 y
2026 (una sola consulta por jugador, cubre ambas temporadas).

Fase 2: por cada temporada que ese jugador necesita, elige el snapshot más
cercano a mitad de esa temporada y descarga su HTML crudo, parseando
"Contrato hasta" directo del header de la página.

El slug de cada jugador (ej. "raphinha") se obtiene de los HTML de plantillas
que ya tenemos descargados en data/raw/transfermarkt/plantillas_html/ -- no
se hace ningún request nuevo al sitio en vivo de Transfermarkt.

Verificado antes de este script (ver conversación): 2 workers en paralelo
sobre HTTPS con sesión persistente es estable; con 6 workers sobre HTTP
aparecieron errores de conexión rechazada -- archive.org no tolera mucha
concurrencia desde un mismo cliente.

Uso:
    python scripts/descargar_contrato_wayback.py
"""
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
import csv
import re
import time

import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
PLANTILLAS = ROOT / "data/raw/transfermarkt/plantillas_html"
OUT = ROOT / "data/raw/wayback_contratos"
HTML_OUT = OUT / "paginas_html"
HTML_OUT.mkdir(parents=True, exist_ok=True)
RESULTADO_CSV = OUT / "contratos.csv"

TEMPORADAS_OBJETIVO = {
    "2024-2025": "20250115000000",  # mitad de temporada, ventana de invierno ya cerrada
    "2025-2026": "20260115000000",
}
VENTANA_MESES = 5  # tolerancia máxima del snapshot elegido respecto a la fecha objetivo

UA = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) research-script diego-diplomado"}
WORKERS = 2
REINTENTOS = 3
TIMEOUT_CDX = 45  # el endpoint CDX de Wayback es lento y variable (visto hasta ~30s)
TIMEOUT_PAGINA = 30

MESES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "octubre": 10, "noviembre": 11,
    "diciembre": 12,
}


def cargar_id_a_slug():
    """Extrae player_id -> slug de las plantillas de Transfermarkt ya descargadas."""
    id_a_slug = {}
    for f in PLANTILLAS.glob("*.html"):
        html = f.read_text(encoding="utf-8", errors="replace")
        for slug, pid in re.findall(r'href="/([a-z0-9-]+)/profil/spieler/(\d+)"', html):
            id_a_slug.setdefault(pid, slug)
    return id_a_slug


def cargar_pendientes(id_a_slug):
    """(player_id, temporada) que necesitan contrato y ya tienen slug conocido."""
    df = pd.read_parquet(ROOT / "data/interim/fbref_tm_dataset.parquet")
    faltan = df[df["Season"].isin(TEMPORADAS_OBJETIVO)][["player_id", "Season"]].drop_duplicates()
    faltan = faltan[faltan["player_id"].isin(id_a_slug)]
    return list(faltan.itertuples(index=False, name=None))


def ya_procesados():
    if not RESULTADO_CSV.exists():
        return set()
    with RESULTADO_CSV.open(encoding="utf-8") as f:
        return {(r["player_id"], r["temporada"]) for r in csv.DictReader(f)}


def sesion_con_reintentos():
    s = requests.Session()
    s.headers.update(UA)
    return s


def cdx_snapshots(sesion, slug, pid):
    """Lista de timestamps de snapshots 200 de la ficha del jugador entre 2024 y 2026.

    Devuelve None (no [] ) si las 3 consultas fallaron -- así el llamador puede
    distinguir "confirmado que no hay snapshots" de "no se pudo consultar", y
    NO escribir una fila falsa que el resumable luego trataría como definitiva.
    """
    url = f"transfermarkt.mx/{slug}/profil/spieler/{pid}"
    endpoint = (
        f"https://web.archive.org/cdx/search/cdx?url={url}"
        "&output=json&from=2024&to=2026&filter=statuscode:200&collapse=timestamp:6"
    )
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion.get(endpoint, timeout=TIMEOUT_CDX)
            if r.status_code == 200:
                filas = r.json()
                return [fila[1] for fila in filas[1:]]  # filas[0] es el header
        except Exception:
            pass
        time.sleep(2 * intento)
    return None


def _a_fecha(timestamp):
    return pd.Timestamp(
        year=int(timestamp[0:4]), month=int(timestamp[4:6]), day=int(timestamp[6:8])
    )


def elegir_snapshot(snapshots, temporada):
    if not snapshots:
        return None
    objetivo = _a_fecha(TEMPORADAS_OBJETIVO[temporada])
    mejor = min(snapshots, key=lambda ts: abs((_a_fecha(ts) - objetivo).days))
    dias = abs((_a_fecha(mejor) - objetivo).days)
    if dias > VENTANA_MESES * 31:
        return None
    return mejor


def parsear_contrato_hasta(html):
    m = re.search(r"Contrato hasta[^\d]*(\d{1,2}/\d{1,2}/\d{4})", html)
    if not m:
        return None
    dia, mes, anio = m.group(1).split("/")
    return pd.Timestamp(year=int(anio), month=int(mes), day=int(dia))


def descargar_snapshot(sesion, slug, pid, timestamp, temporada):
    """Devuelve (contrato_o_None, ok). ok=False = falló la descarga (reintentar
    después); ok=True = se bajó la página, contrato_o_None ya es definitivo
    (None significa que Transfermarkt mostraba "-" en ese campo, dato real)."""
    destino = HTML_OUT / f"{pid}_{temporada}.html"
    if destino.exists():
        html = destino.read_text(encoding="utf-8", errors="replace")
        return parsear_contrato_hasta(html), True

    url = f"https://web.archive.org/web/{timestamp}/https://www.transfermarkt.mx/{slug}/profil/spieler/{pid}"
    for intento in range(1, REINTENTOS + 1):
        try:
            r = sesion.get(url, timeout=TIMEOUT_PAGINA)
            if r.status_code == 200:
                r.encoding = "utf-8"
                destino.write_text(r.text, encoding="utf-8")
                return parsear_contrato_hasta(r.text), True
        except Exception:
            pass
        time.sleep(2 * intento)
    return None, False


def procesar_jugador(pid, temporadas, id_a_slug):
    """Devuelve lista de dicts {player_id, temporada, contrato_vence, snapshot} SOLO
    para las temporadas con respuesta definitiva -- las que fallaron por red/timeout
    no se incluyen, para que una corrida futura las reintente (ver ya_procesados)."""
    sesion = sesion_con_reintentos()
    slug = id_a_slug[pid]
    snapshots = cdx_snapshots(sesion, slug, pid)

    if snapshots is None:
        return []  # no se pudo consultar CDX -- reintentar todo este jugador después

    resultados = []
    for temporada in temporadas:
        ts = elegir_snapshot(snapshots, temporada)
        if ts is None:
            # confirmado (CDX sí respondió): no hay snapshot útil en la ventana
            resultados.append({"player_id": pid, "temporada": temporada,
                                "contrato_vence": "", "snapshot": ""})
            continue
        contrato, ok = descargar_snapshot(sesion, slug, pid, ts, temporada)
        if not ok:
            continue  # falló la descarga -- reintentar esta temporada después
        resultados.append({
            "player_id": pid, "temporada": temporada,
            "contrato_vence": contrato.date().isoformat() if contrato else "",
            "snapshot": ts,
        })
    return resultados


def main():
    id_a_slug = cargar_id_a_slug()
    print(f"player_id -> slug conocidos: {len(id_a_slug)}", flush=True)

    pendientes = cargar_pendientes(id_a_slug)
    hechos = ya_procesados()
    pendientes = [(pid, t) for pid, t in pendientes if (pid, t) not in hechos]

    por_jugador = {}
    for pid, temporada in pendientes:
        por_jugador.setdefault(pid, []).append(temporada)

    print(f"Jugadores por procesar: {len(por_jugador)} "
          f"({len(pendientes)} pares jugador-temporada)", flush=True)

    nuevo_archivo = not RESULTADO_CSV.exists()
    with RESULTADO_CSV.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["player_id", "temporada", "contrato_vence", "snapshot"])
        if nuevo_archivo:
            writer.writeheader()
            f.flush()

        n = 0
        sin_filas = 0
        total = len(por_jugador)
        with ThreadPoolExecutor(max_workers=WORKERS) as ex:
            futuros = {
                ex.submit(procesar_jugador, pid, temporadas, id_a_slug): (pid, temporadas)
                for pid, temporadas in por_jugador.items()
            }
            for fut in as_completed(futuros):
                n += 1
                pid, temporadas = futuros[fut]
                try:
                    filas = fut.result()
                except Exception as e:
                    print(f"[{n}/{total}] FALLO {pid}: {e!r}", flush=True)
                    continue
                if not filas:
                    sin_filas += 1  # CDX falló para este jugador -- se reintenta en la próxima corrida
                for fila in filas:
                    writer.writerow(fila)
                f.flush()
                if n % 25 == 0 or n == total:
                    print(f"[{n}/{total}] procesados (último: {pid}, "
                          f"sin respuesta definitiva hasta ahora: {sin_filas})", flush=True)

    print("Terminado.", flush=True)


if __name__ == "__main__":
    main()
