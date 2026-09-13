from pydantic import BaseModel


class TemporadaRendimiento(BaseModel):
    temporada: str
    saison_id: int
    club: str
    goles: int
    tiros: int
    tarjetas_amarillas: int
    asistencias: int
    valor_mercado_eur: float


class HistorialJugador(BaseModel):
    player_id: str
    nombre: str
    temporadas: list[TemporadaRendimiento]
