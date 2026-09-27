from pydantic import BaseModel


class TemporadaRendimiento(BaseModel):
    temporada: str
    saison_id: int
    club: str
    goles: int
    tiros: int
    tarjetas_amarillas: int
    tarjetas_rojas: int
    asistencias: int
    minutos_jugados: int
    entradas_ganadas: int
    intercepciones: int
    valor_mercado_eur: float


class HistorialJugador(BaseModel):
    player_id: str
    nombre: str
    temporadas: list[TemporadaRendimiento]
