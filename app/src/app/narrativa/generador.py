import json

from openai import OpenAI

from app.schemas.comparacion import ComparacionJugadores

SYSTEM_PROMPT = (
    "Eres un analista de scouting de fútbol. Se te entrega una comparación ya calculada "
    "entre dos jugadores: percentiles frente a jugadores de su misma posición y temporada, "
    "la contribución de un modelo de valor de mercado a la diferencia de valor entre ambos, "
    "y su arquetipo de estilo de juego (de un modelo de clustering). Tu único trabajo es "
    "REDACTAR esa comparación en español de forma clara, objetiva y con suficiente detalle "
    "para un scout: no te limites a listar los datos, conéctalos entre sí (por ejemplo, "
    "relaciona un percentil alto en una estadística con el arquetipo de estilo de juego, o "
    "con los factores que explican la diferencia de valor) para dar una lectura más completa.\n\n"
    "Reglas estrictas:\n"
    "- No inventes cifras, estadísticas ni hechos que no estén en los datos entregados.\n"
    "- No calcules nada nuevo: limita tus afirmaciones a lo que los números ya indican.\n"
    "- El valor de mercado es una estimación de un modelo estadístico, no una tasación "
    "oficial ni una recomendación de compra o venta: trátalo siempre como estimación.\n"
    "- Si los dos jugadores juegan posiciones distintas, acláralo antes de comparar percentiles.\n"
    "- Cada factor de 'factores_que_explican_la_diferencia_de_valor' ya trae el nombre exacto "
    "del jugador al que favorece en 'jugador_favorecido': atribúyeselo literalmente a ese "
    "jugador, nunca al otro."
)

RESPONSE_SCHEMA = {
    "name": "narrativa_comparacion",
    "schema": {
        "type": "object",
        "properties": {
            "resumen": {
                "type": "string",
                "description": (
                    "5-7 oraciones que sintetizan la comparación completa: incluye posición, "
                    "estilo de juego (arquetipo) y una lectura general de las diferencias de "
                    "rendimiento y de valor de mercado entre ambos jugadores."
                ),
            },
            "fortalezas_jugador_a": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "4 a 6 puntos donde el jugador A destaca sobre el B. Cada punto debe ser "
                    "1-2 oraciones: no solo nombrar la estadística, sino explicar qué implica "
                    "esa diferencia para el estilo de juego o el rol del jugador en la cancha."
                ),
            },
            "fortalezas_jugador_b": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "4 a 6 puntos donde el jugador B destaca sobre el A. Cada punto debe ser "
                    "1-2 oraciones: no solo nombrar la estadística, sino explicar qué implica "
                    "esa diferencia para el estilo de juego o el rol del jugador en la cancha."
                ),
            },
            "explicacion_diferencia_valor": {
                "type": "string",
                "description": (
                    "4-6 oraciones que explican en detalle la brecha de valor de mercado, "
                    "citando y desarrollando cada uno de los factores entregados en "
                    "'factores_que_explican_la_diferencia_de_valor' y a qué jugador favorece."
                ),
            },
        },
        "required": [
            "resumen",
            "fortalezas_jugador_a",
            "fortalezas_jugador_b",
            "explicacion_diferencia_valor",
        ],
        "additionalProperties": False,
    },
    "strict": True,
}


def _datos_para_prompt(comparacion: ComparacionJugadores) -> dict:
    a, b = comparacion.jugador_a, comparacion.jugador_b
    valor = comparacion.valor
    arquetipo = comparacion.arquetipo
    return {
        "jugador_a": {
            "nombre": a.nombre,
            "club": a.club,
            "posicion": a.posicion_detallada,
            "edad": a.edad,
            "temporada": a.temporada,
        },
        "jugador_b": {
            "nombre": b.nombre,
            "club": b.club,
            "posicion": b.posicion_detallada,
            "edad": b.edad,
            "temporada": b.temporada,
        },
        "misma_posicion": comparacion.grupo_comparacion_a.posicion == comparacion.grupo_comparacion_b.posicion,
        "percentiles_vs_su_posicion": [
            {
                "estadistica": p.etiqueta,
                "percentil_a": round(p.percentil_a * 100, 1),
                "percentil_b": round(p.percentil_b * 100, 1),
            }
            for p in comparacion.percentiles
        ],
        "valor_estimado_eur": {
            "medio_a": round(valor.banda_a.valor_medio),
            "medio_b": round(valor.banda_b.valor_medio),
        },
        "factores_que_explican_la_diferencia_de_valor": [
            {
                "factor": c.etiqueta,
                "jugador_favorecido": a.nombre if c.diferencia_log > 0 else b.nombre,
            }
            for c in valor.contribuciones_diferencia
        ],
        "arquetipo_estilo_de_juego": {
            "jugador_a": arquetipo.etiqueta_a,
            "jugador_b": arquetipo.etiqueta_b,
            "mismo_arquetipo": arquetipo.mismo_arquetipo,
        },
    }


class NarradorComparacion:
    """Redacta en prosa una comparación entre dos jugadores ya calculada por la app.

    El LLM no recibe datos crudos ni hace ningún cálculo: solo interpreta el JSON de
    diferencias (percentiles, contribuciones del Lasso, arquetipo) que ya produjo
    `comparar_jugadores`. Así el texto nunca puede inventar un número que el modelo no
    haya calculado.
    """

    def __init__(self, api_key: str, modelo: str = "gpt-4.1"):
        self._client = OpenAI(api_key=api_key)
        self._modelo = modelo

    def redactar(self, comparacion: ComparacionJugadores) -> dict:
        datos = _datos_para_prompt(comparacion)
        respuesta = self._client.chat.completions.create(
            model=self._modelo,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": json.dumps(datos, ensure_ascii=False)},
            ],
            response_format={"type": "json_schema", "json_schema": RESPONSE_SCHEMA},
        )
        return json.loads(respuesta.choices[0].message.content)
