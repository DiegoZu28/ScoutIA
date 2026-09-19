"""Traducción al español de las posiciones (columnas Pos y posicion_tm del dataset).

Puramente de presentación: el pipeline de modelado nunca lee estas columnas en
texto (usa las dummies pos_* / _rs ya precomputadas en dataset.parquet), así
que traducirlas acá no afecta ninguna predicción.
"""

# posicion_tm (Transfermarkt, más granular) -> nombres tal como los usa la propia
# Transfermarkt en su sitio en español.
POSICIONES_DETALLADAS: dict[str, str] = {
    "Goalkeeper": "Portero",
    "Centre-Back": "Defensa central",
    "Left-Back": "Lateral izquierdo",
    "Right-Back": "Lateral derecho",
    "Defensive Midfield": "Pivote",
    "Central Midfield": "Centrocampista",
    "Attacking Midfield": "Mediapunta",
    "Left Midfield": "Interior izquierdo",
    "Right Midfield": "Interior derecho",
    "Left Winger": "Extremo izquierdo",
    "Right Winger": "Extremo derecho",
    "Second Striker": "Segundo delantero",
    "Centre-Forward": "Delantero centro",
}

# Pos (FBref, código corto; puede venir combinado ej. "DF,MF" en multiposicionales)
POSICIONES_CORTAS: dict[str, str] = {
    "GK": "POR",
    "DF": "DEF",
    "MF": "MED",
    "FW": "DEL",
}


def posicion_detallada_es(posicion_tm: str) -> str:
    return POSICIONES_DETALLADAS.get(posicion_tm, posicion_tm)


def posicion_corta_es(pos: str) -> str:
    return ",".join(POSICIONES_CORTAS.get(token, token) for token in pos.split(","))
