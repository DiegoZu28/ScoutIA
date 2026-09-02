"""Parseo de las plantillas descargadas de Transfermarkt."""

import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


def _texto(fila, i):
    """Texto de la celda i, o cadena vacía si no existe."""
    tds = fila.find_all("td", recursive=False)
    return tds[i].get_text(" ", strip=True) if i < len(tds) else ""


def parsear_valor(txt):
    """'€10.00m' -> 10_000_000 ; '€500k' -> 500_000 ; '-' -> None."""
    if not txt:
        return None
    t = txt.replace("\xa0", " ").strip().lower()
    m = re.search(r"([\d.,]+)\s*([mk])?", t.replace("€", ""))
    if not m:
        return None
    num = m.group(1).replace(",", "")
    try:
        valor = float(num)
    except ValueError:
        return None
    sufijo = m.group(2)
    if sufijo == "m":
        valor *= 1_000_000
    elif sufijo == "k":
        valor *= 1_000
    return valor if valor > 0 else None


def parsear_fecha_nacimiento(txt):
    """'29/09/2000 (21)' -> ('29/09/2000', 21)."""
    if not txt:
        return None, None
    m = re.search(r"(\d{2}/\d{2}/\d{4})", txt)
    fecha = m.group(1) if m else None
    m2 = re.search(r"\((\d+)\)", txt)
    edad = int(m2.group(1)) if m2 else None
    return fecha, edad


def parsear_altura(txt):
    """'1,97m' -> 1.97"""
    if not txt:
        return None
    m = re.search(r"(\d)[,.](\d{2})", txt)
    return float(f"{m.group(1)}.{m.group(2)}") if m else None


def parsear_plantilla(ruta):
    """Parsea un HTML de plantilla y devuelve un DataFrame."""
    ruta = Path(ruta)
    soup = BeautifulSoup(ruta.read_text(encoding="utf-8"), "lxml")

    tabla = soup.select_one("table.items")
    if tabla is None:
        return pd.DataFrame()

    tbody = tabla.find("tbody")
    if tbody is None:
        return pd.DataFrame()

    # Solo hijos directos: evita las tablas anidadas dentro de las celdas
    filas = tbody.find_all("tr", recursive=False)

    # liga_temporada_club vienen del nombre del archivo
    partes = ruta.stem.split("_")
    liga_codigo, saison_id, club_id = partes[0], int(partes[1]), partes[2]

    registros = []
    for fila in filas:
        link = fila.select_one("a[href*='/profil/spieler/']")
        if link is None:
            continue  # fila de encabezado o pie

        m = re.search(r"/profil/spieler/(\d+)", link["href"])
        if not m:
            continue

        tds = fila.find_all("td", recursive=False)
        nacimiento, edad = parsear_fecha_nacimiento(_texto(fila, 2))

        # Nacionalidad: viene como atributo title de las banderitas
        naciones = []
        for td in tds:
            for img in td.select("img.flaggenrahmen"):
                t = img.get("title")
                if t and t not in naciones:
                    naciones.append(t)

        # La posicion vive en la tabla anidada de la celda 1,
        # en la segunda fila interna (la primera es el nombre)
        posicion = None
        if len(tds) > 1:
            internas = [tr.get_text(" ", strip=True) for tr in tds[1].select("tr")]
            if len(internas) > 1:
                posicion = internas[1]

        registros.append({
            "player_id": m.group(1),
            "player_tm": link.get_text(strip=True),
            "dorsal": _texto(fila, 0),
            "posicion_tm": posicion,
            "nacimiento": nacimiento,
            "edad_tm": edad,
            "nacionalidad": naciones[0] if naciones else None,
            "altura_m": parsear_altura(_texto(fila, 5)),
            "pie": _texto(fila, 6),
            "fecha_fichaje": _texto(fila, 7),
            "valor_eur": parsear_valor(_texto(fila, 9)),
            "liga_codigo": liga_codigo,
            "saison_id": saison_id,
            "club_id": club_id,
        })

    return pd.DataFrame(registros)


def parsear_todas(carpeta):
    """Parsea todas las plantillas de una carpeta y las concatena."""
    carpeta = Path(carpeta)
    partes = []
    for archivo in sorted(carpeta.glob("*.html")):
        df = parsear_plantilla(archivo)
        if df.empty:
            print("VACIO", archivo.name)
        partes.append(df)
    return pd.concat(partes, ignore_index=True) if partes else pd.DataFrame()