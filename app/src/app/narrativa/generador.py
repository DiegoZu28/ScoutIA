import json

from openai import OpenAI

from app.schemas.comparacion import ComparacionJugadores

SYSTEM_PROMPT = (
    "Eres un analista de scouting de fútbol. Se te entrega una comparación ya calculada "
    "entre dos jugadores: qué tan bien rinde cada uno frente a otros de su misma posición y "
    "temporada, la contribución de un modelo de valor de mercado a la diferencia de valor "
    "entre ambos, y su arquetipo de estilo de juego (de un modelo de clustering). Tu único "
    "trabajo es REDACTAR esa comparación en español de forma clara, objetiva y CONCISA para "
    "un scout: ve directo a lo importante (fortalezas de cada uno y por qué difiere el "
    "valor), sin relleno ni frases genéricas.\n\n"
    "Reglas estrictas:\n"
    "- No inventes cifras, estadísticas ni hechos que no estén en los datos entregados.\n"
    "- No calcules nada nuevo: limita tus afirmaciones a lo que los números ya indican.\n"
    "- El valor de mercado es una estimación de un modelo estadístico, no una tasación "
    "oficial ni una recomendación de compra o venta: trátalo siempre como estimación.\n"
    "- Si los dos jugadores juegan posiciones distintas, acláralo antes de comparar su "
    "rendimiento relativo.\n"
    "- En 'rendimiento_frente_a_su_posicion' cada estadística trae 'nivel_a'/'nivel_b', un "
    "valor de 0 a 100 que indica qué tan bien rinde cada jugador frente a otros de su misma "
    "posición y temporada (más alto = mejor). Redáctalo siempre en lenguaje cotidiano, no "
    "estadístico: nunca escribas la palabra 'percentil' ni cites el número exacto en la "
    "prosa -- usa expresiones como 'está entre los mejores de su posición', 'rinde muy por "
    "encima/debajo del promedio' o 'destaca claramente' según qué tan alto o bajo sea el "
    "valor.\n"
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
                    "1-2 oraciones que sitúan la comparación (posición y arquetipo de cada "
                    "uno, y si son directamente comparables). Nada más -- el detalle va en "
                    "fortalezas y en la explicación de valor, no acá."
                ),
            },
            "fortalezas_jugador_a": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "2 a 3 puntos donde el jugador A destaca sobre el B. Cada punto: una sola "
                    "oración, directa, que nombre la estadística y qué implica."
                ),
            },
            "fortalezas_jugador_b": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "2 a 3 puntos donde el jugador B destaca sobre el A. Cada punto: una sola "
                    "oración, directa, que nombre la estadística y qué implica."
                ),
            },
            "explicacion_diferencia_valor": {
                "type": "string",
                "description": (
                    "2-3 oraciones que expliquen la brecha de valor de mercado citando los "
                    "factores de 'factores_que_explican_la_diferencia_de_valor' más relevantes "
                    "(no hace falta nombrarlos todos) y a qué jugador favorecen."
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
        "rendimiento_frente_a_su_posicion": [
            {
                "estadistica": p.etiqueta,
                "nivel_a": round(p.percentil_a * 100, 1),
                "nivel_b": round(p.percentil_b * 100, 1),
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
