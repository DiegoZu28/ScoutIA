from pydantic import BaseModel


class PercentilEstadistica(BaseModel):
    estadistica: str
    etiqueta: str
    percentil: float
    valor_bruto: float


class GrupoComparacion(BaseModel):
    posicion: str
    temporada: str
    n: int


class PercentilesJugador(BaseModel):
    grupo_comparacion: GrupoComparacion
    percentiles: list[PercentilEstadistica]
