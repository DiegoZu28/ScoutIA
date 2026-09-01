"""Descarga estadísticas Big5 de FBref (todas las categorías)."""
from pathlib import Path
from io import StringIO
import time
import pandas as pd
from bs4 import BeautifulSoup, Comment
import soccerdata as sd

OUT = Path("data/raw/fbref_big5")
OUT.mkdir(parents=True, exist_ok=True)

TEMPORADAS = ['2021-2022', '2022-2023', '2023-2024', '2024-2025', '2025-2026']
TIPOS = ['stats', 'shooting', 'playingtime', 'misc']

# Los ids de tabla de FBref no siempre coinciden con el segmento de la URL
IDS_TABLA = {
    'stats': 'stats_standard',
    'shooting': 'stats_shooting',
    'playingtime': 'stats_playing_time',
    'misc': 'stats_misc',
}


def buscar_tabla(soup, id_tabla):
    """Busca la tabla en el HTML normal y dentro de comentarios."""
    tabla = soup.find("table", {"id": id_tabla})
    if tabla is not None:
        return tabla
    for c in soup.find_all(string=lambda t: isinstance(t, Comment)):
        tabla = BeautifulSoup(c, "lxml").find("table", {"id": id_tabla})
        if tabla is not None:
            return tabla
    return None


def main():
    fb = sd.FBref(leagues='ENG-Premier League', seasons='2425')
    drv = fb._driver

    total = len(TEMPORADAS) * len(TIPOS)
    n = 0

    try:
        for temp in TEMPORADAS:
            for tipo in TIPOS:
                n += 1
                archivo = OUT / f"big5_{temp}_{tipo}.parquet"
                if archivo.exists():
                    print(f"[{n}/{total}] SALTADO {archivo.name}", flush=True)
                    continue

                url = (f"https://fbref.com/en/comps/Big5/{temp}/{tipo}/players/"
                       f"{temp}-Big-5-European-Leagues-Stats")
                try:
                    drv.get(url)
                    time.sleep(10)
                    html = drv.page_source

                    # Respaldo crudo: si el parseo falla, no hay que volver a bajar
                    (OUT / f"big5_{temp}_{tipo}.html").write_text(html, encoding="utf-8")

                    soup = BeautifulSoup(html, "lxml")
                    tabla = buscar_tabla(soup, IDS_TABLA[tipo])

                    if tabla is None:
                        ids = [t.get("id") for t in soup.find_all("table")]
                        print(f"[{n}/{total}] SIN TABLA {archivo.name} | ids: {ids}",
                              flush=True)
                        continue

                    df = pd.read_html(StringIO(str(tabla)))[0]
                    df.to_parquet(archivo)
                    print(f"[{n}/{total}] OK {archivo.name} -> {df.shape}", flush=True)

                except Exception as e:
                    print(f"[{n}/{total}] FALLO {archivo.name}: {e!r}", flush=True)
    finally:
        try:
            drv.quit()
        except Exception:
            pass
        print("Terminado.", flush=True)


if __name__ == "__main__":
    main()