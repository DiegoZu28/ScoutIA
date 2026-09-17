from pydantic import BaseModel

from app.schemas.jugador import EstadisticasJugador
from app.schemas.percentiles import GrupoComparacion
from app.schemas.valor import NOTA_METODOLOGIA, BandaValor


class PercentilComparado(BaseModel):
    estadistica: str
    etiqueta: str
    percentil_a: float
    percentil_b: float
    valor_bruto_a: float
    valor_bruto_b: float
    diferencia: float  # percentil_a - percentil_b


class ContribucionComparada(BaseModel):
    feature: str
    etiqueta: str
    contribucion_log_a: float
    contribucion_log_b: float
    diferencia_log: float  # contribucion_log_a - contribucion_log_b


class ArquetipoComparado(BaseModel):
    cluster_id_a: int
    etiqueta_a: str
    cluster_id_b: int
    etiqueta_b: str
    mismo_arquetipo: bool


class ValorComparado(BaseModel):
    banda_a: BandaValor
    banda_b: BandaValor
    diferencia_valor_medio_eur: float  # valor_medio_a - valor_medio_b
    contribuciones_diferencia: list[ContribucionComparada]
    metodologia_nota: str = NOTA_METODOLOGIA


class ComparacionJugadores(BaseModel):
    jugador_a: EstadisticasJugador
    jugador_b: EstadisticasJugador
    grupo_comparacion_a: GrupoComparacion
    grupo_comparacion_b: GrupoComparacion
    percentiles: list[PercentilComparado]
    valor: ValorComparado
    arquetipo: ArquetipoComparado


class NarrativaComparacion(BaseModel):
    resumen: str
    fortalezas_jugador_a: list[str]
    fortalezas_jugador_b: list[str]
    explicacion_diferencia_valor: str
    metodologia_nota: str = NOTA_METODOLOGIA
