from pydantic import BaseModel


class JugadorBusqueda(BaseModel):
    player_id: str
    nombre: str
    club: str
    posicion: str
    liga: str
    temporada_mas_reciente: str


class EstadisticasJugador(BaseModel):
    player_id: str
    nombre: str
    club: str
    nacionalidad: str
    posicion: str
    posicion_detallada: str
    liga: str
    temporada: str
    edad: float
    minutos_jugados: int
    goles: int
    asistencias: int
    tiros: int
    tarjetas_amarillas: int
    valor_mercado_eur: float
    contrato_conocido: bool
    dias_contrato_restante: float | None
    gano_liga: bool
    gano_champions: bool
