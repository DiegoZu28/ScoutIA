import pandas as pd

from app.valuation.predictor import Predictor


def calcular_oportunidades(df_vigentes: pd.DataFrame, predictor: Predictor, limit: int) -> pd.DataFrame:
    """Jugadores vigentes cuya banda de valor (modelo) está por encima de su valor de Transfermarkt.

    Ordenados por la brecha absoluta (valor medio estimado - valor de mercado) descendente.
    `banda_completa_por_encima` marca la señal más confiable: cuando incluso el extremo bajo
    de la banda ya supera el valor de mercado, no solo el punto medio.
    """
    banda = predictor.predecir_banda_lote(df_vigentes)
    resultado = df_vigentes.copy()
    resultado["valor_bajo"] = banda["valor_bajo"]
    resultado["valor_medio"] = banda["valor_medio"]
    resultado["valor_alto"] = banda["valor_alto"]
    resultado["diferencia_eur"] = resultado["valor_medio"] - resultado["valor_eur"]
    resultado["diferencia_pct"] = resultado["diferencia_eur"] / resultado["valor_eur"]
    resultado["banda_completa_por_encima"] = resultado["valor_bajo"] > resultado["valor_eur"]

    candidatos = resultado[resultado["valor_medio"] > resultado["valor_eur"]]
    return candidatos.sort_values("diferencia_eur", ascending=False).head(limit)
