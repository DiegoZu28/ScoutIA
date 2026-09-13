"""Nombres legibles en español para las columnas crudas del dataset (usadas en contribuciones y percentiles)."""

FEATURE_LABELS: dict[str, str] = {
    "Age_rs": "Edad",
    "altura_m_rs": "Altura",
    "Playing Time_Min_rs": "Minutos jugados",
    "Performance_Gls_rs": "Goles",
    "Performance_Ast_rs": "Asistencias",
    "Standard_Sh_rs": "Tiros totales",
    "Performance_CrdY_rs": "Tarjetas amarillas",
    "Team Success_PPM_rs": "Puntos por partido del equipo",
    "Squad_target_enc": "Fuerza histórica del equipo",
    "Per 90 Minutes_Gls": "Goles por 90'",
    "Per 90 Minutes_Ast": "Asistencias por 90'",
    "Standard_SoT%": "% de tiros a puerta",
    "Standard_Sh/90": "Tiros por 90'",
    "Standard_SoT/90": "Tiros a puerta por 90'",
    "Standard_G/Sh": "Goles por tiro",
    "Standard_G/SoT": "Goles por tiro a puerta",
    "Performance_TklW": "Entradas ganadas",
    "Performance_Int": "Intercepciones",
    "Performance_Crs": "Centros",
    "Performance_Fld": "Faltas recibidas",
    "Performance_Off": "Fueras de lugar",
    "Performance_PK": "Penales anotados",
    "Performance_PKatt": "Penales intentados",
    "Performance_CrdR": "Tarjetas rojas",
    "Performance_2CrdY": "Doble amarilla",
    "Performance_OG": "Goles en propia meta",
    "Playing Time_Mn/MP": "Minutos por partido",
    "Playing Time_Min%": "% de minutos disputados",
    "Starts_Mn/Start": "Minutos por titularidad",
    "Subs_Subs": "Veces de sustituto",
    "Subs_Mn/Sub": "Minutos por sustitución",
    "Subs_unSub": "Veces no utilizado",
    "Team Success_onG": "Goles del equipo con el jugador en cancha",
    "Team Success_onGA": "Goles recibidos con el jugador en cancha",
    "Team Success_On-Off": "Diferencial on/off del equipo",
    "flag_sin_tiros": "Sin registro de tiros",
    "flag_sin_titularidades": "Sin registro de titularidades",
    "flag_sin_suplencias": "Sin registro de suplencias",
    "dias_contrato_restante": "Tiempo restante de contrato",
    "flag_contrato_conocido": "Contrato conocido",
    "log1p_Standard_SoT": "Tiros a puerta (transformado)",
    "log1p_Performance_Crs": "Centros (transformado)",
    "log1p_Performance_Fls": "Faltas cometidas (transformado)",
    "Ganador_Champions": "Ganó la Champions esa temporada",
    "Ganador_Liga": "Ganó la liga esa temporada",
}


def etiqueta_legible(feature: str) -> str:
    if feature in FEATURE_LABELS:
        return FEATURE_LABELS[feature]
    if feature.startswith("pos_"):
        return "Posición: " + feature.removeprefix("pos_")
    if feature.startswith("liga_"):
        return "Liga: " + feature.removeprefix("liga_")
    return feature.replace("_", " ").strip()
