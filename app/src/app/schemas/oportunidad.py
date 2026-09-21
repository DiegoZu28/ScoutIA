from pydantic import BaseModel

from app.schemas.valor import BandaValor

NOTA_METODOLOGIA_OPORTUNIDADES = (
    "Compara la banda de valor estimada por el modelo con el valor de mercado publicado en "
    "Transfermarkt. Un valor estimado por encima del de mercado no es una recomendación de "
    "compra o venta: son casos a revisión manual, ya que el modelo puede no capturar factores "
    "como lesiones, contexto táctico o situación contractual."
)


class OportunidadJugador(BaseModel):
    player_id: str
    nombre: str
    club: str
    posicion: str
    liga: str
    temporada: str
    foto_url: str | None = None
    valor_mercado_eur: float
    banda: BandaValor
    diferencia_eur: float
    diferencia_pct: float
    banda_completa_por_encima: bool


class ListaOportunidades(BaseModel):
    jugadores: list[OportunidadJugador]
    metodologia_nota: str = NOTA_METODOLOGIA_OPORTUNIDADES
