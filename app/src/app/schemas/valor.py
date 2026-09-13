from pydantic import BaseModel

NOTA_METODOLOGIA = (
    "Estimación de un modelo estadístico entrenado con datos históricos de rendimiento y "
    "valor de mercado. No es una tasación oficial ni una recomendación de compra o venta: "
    "preséntese siempre como rango, nunca como cifra puntual."
)


class BandaValor(BaseModel):
    valor_bajo: float
    valor_medio: float
    valor_alto: float
    moneda: str = "EUR"


class ContribucionVariable(BaseModel):
    feature: str
    etiqueta: str
    contribucion_log: float
    valor_bruto_jugador: float
    direccion: str


class PrediccionValor(BaseModel):
    banda: BandaValor
    contribuciones: list[ContribucionVariable]
    metodologia_nota: str = NOTA_METODOLOGIA
