import pandas as pd
from fastapi import APIRouter, HTTPException, Query, Request

from app.domain.dataset_repository import DatasetRepository
from app.domain.exceptions import JugadorNoEncontrado, TemporadaNoEncontrada
from app.domain.feature_labels import etiqueta_legible
from app.schemas.arquetipo import ArquetipoJugador
from app.schemas.historial import HistorialJugador, TemporadaRendimiento
from app.schemas.jugador import EstadisticasJugador, JugadorBusqueda
from app.schemas.percentiles import GrupoComparacion, PercentilEstadistica, PercentilesJugador
from app.schemas.valor import BandaValor, ContribucionVariable, PrediccionValor
from app.valuation.predictor import Predictor

router = APIRouter(prefix="/jugadores", tags=["jugadores"])

# Mismo subconjunto de estadísticas usado en scripts/build_model_artifacts.py para calcular
# las columnas pctl_*.
PERCENTILE_STATS = [
    "Per 90 Minutes_Gls",
    "Per 90 Minutes_Ast",
    "Standard_Sh/90",
    "Standard_SoT%",
    "Performance_TklW",
    "Performance_Int",
    "Performance_Crs",
    "Playing Time_Min%",
]


def _repo(request: Request) -> DatasetRepository:
    return request.app.state.dataset_repository


def _predictor(request: Request) -> Predictor:
    return request.app.state.predictor


def _resolver_fila(request: Request, player_id: str, temporada: int | None) -> pd.Series:
    try:
        return _repo(request).obtener_fila(player_id, temporada)
    except JugadorNoEncontrado as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except TemporadaNoEncontrada as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


def _estadisticas_de(player_id: str, fila: pd.Series) -> EstadisticasJugador:
    contrato_conocido = bool(fila["flag_contrato_conocido"])
    return EstadisticasJugador(
        player_id=player_id,
        nombre=str(fila["Player"]),
        club=str(fila["Squad"]),
        nacionalidad=str(fila["Nation"]),
        posicion=str(fila["Pos"]),
        posicion_detallada=str(fila["posicion_tm"]),
        liga=str(fila["Comp"]),
        temporada=str(fila["Season"]),
        edad=float(fila["Age"]),
        minutos_jugados=int(fila["Playing Time_Min"]),
        goles=int(fila["Performance_Gls"]),
        asistencias=int(fila["Performance_Ast"]),
        tiros=int(fila["Standard_Sh"]),
        tarjetas_amarillas=int(fila["Performance_CrdY"]),
        valor_mercado_eur=float(fila["valor_eur"]),
        contrato_conocido=contrato_conocido,
        dias_contrato_restante=float(fila["dias_contrato_restante"]) if contrato_conocido else None,
        gano_liga=bool(fila["Ganador_Liga"]),
        gano_champions=bool(fila["Ganador_Champions"]),
    )


def _historial_de(player_id: str, filas: pd.DataFrame) -> HistorialJugador:
    temporadas = [
        TemporadaRendimiento(
            temporada=str(fila["Season"]),
            saison_id=int(fila["saison_id"]),
            club=str(fila["Squad"]),
            goles=int(fila["Performance_Gls"]),
            tiros=int(fila["Standard_Sh"]),
            tarjetas_amarillas=int(fila["Performance_CrdY"]),
            asistencias=int(fila["Performance_Ast"]),
            valor_mercado_eur=float(fila["valor_eur"]),
        )
        for _, fila in filas.iterrows()
    ]
    return HistorialJugador(
        player_id=player_id,
        nombre=str(filas["Player"].iloc[0]),
        temporadas=temporadas,
    )


def _valor_de(request: Request, fila: pd.Series) -> PrediccionValor:
    predictor = _predictor(request)
    banda = predictor.predecir_banda(fila)
    top_n = request.app.state.settings.top_n_contribuciones
    contribuciones = predictor.explicar(fila, top_n=top_n)
    return PrediccionValor(
        banda=BandaValor(**banda),
        contribuciones=[ContribucionVariable(**c) for c in contribuciones],
    )


def _percentiles_de(fila: pd.Series) -> PercentilesJugador:
    percentiles = [
        PercentilEstadistica(
            estadistica=stat,
            etiqueta=etiqueta_legible(stat),
            percentil=float(fila[f"pctl_{stat}"]),
            valor_bruto=float(fila[stat]),
        )
        for stat in PERCENTILE_STATS
    ]
    return PercentilesJugador(
        grupo_comparacion=GrupoComparacion(
            posicion=str(fila["posicion_tm"]),
            temporada=str(fila["Season"]),
            n=int(fila["n_comparacion"]),
        ),
        percentiles=percentiles,
    )


def _arquetipo_de(fila: pd.Series) -> ArquetipoJugador:
    return ArquetipoJugador(cluster_id=int(fila["cluster_id"]), etiqueta=str(fila["cluster_label"]))


@router.get("/buscar", response_model=list[JugadorBusqueda])
def buscar_jugador(request: Request, q: str = Query(min_length=1), limit: int = 20):
    resultados = _repo(request).buscar(q, limit)
    return [
        JugadorBusqueda(
            player_id=str(player_id),
            nombre=str(fila["Player"]),
            club=str(fila["Squad"]),
            posicion=str(fila["posicion_tm"]),
            liga=str(fila["Comp"]),
            temporada_mas_reciente=str(fila["Season"]),
        )
        for player_id, fila in resultados.iterrows()
    ]


@router.get("/{player_id}/estadisticas", response_model=EstadisticasJugador)
def obtener_estadisticas(request: Request, player_id: str, temporada: int | None = None):
    fila = _resolver_fila(request, player_id, temporada)
    return _estadisticas_de(player_id, fila)


@router.get("/{player_id}/valor", response_model=PrediccionValor)
def predecir_valor(request: Request, player_id: str, temporada: int | None = None):
    fila = _resolver_fila(request, player_id, temporada)
    return _valor_de(request, fila)


@router.get("/{player_id}/percentiles", response_model=PercentilesJugador)
def obtener_percentiles(request: Request, player_id: str, temporada: int | None = None):
    fila = _resolver_fila(request, player_id, temporada)
    return _percentiles_de(fila)


@router.get("/{player_id}/arquetipo", response_model=ArquetipoJugador)
def obtener_arquetipo(request: Request, player_id: str, temporada: int | None = None):
    fila = _resolver_fila(request, player_id, temporada)
    return _arquetipo_de(fila)


@router.get("/{player_id}/historial", response_model=HistorialJugador)
def obtener_historial(request: Request, player_id: str):
    try:
        filas = _repo(request).historial_de(player_id)
    except JugadorNoEncontrado as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return _historial_de(player_id, filas)


@router.get("/{player_id}/ficha")
def obtener_ficha(request: Request, player_id: str, temporada: int | None = None):
    """Combina los 5 endpoints anteriores en una sola llamada (conveniencia de Fase 1)."""
    fila = _resolver_fila(request, player_id, temporada)
    historial = _repo(request).historial_de(player_id)
    return {
        "estadisticas": _estadisticas_de(player_id, fila),
        "valor": _valor_de(request, fila),
        "percentiles": _percentiles_de(fila),
        "arquetipo": _arquetipo_de(fila),
        "historial": _historial_de(player_id, historial),
    }
