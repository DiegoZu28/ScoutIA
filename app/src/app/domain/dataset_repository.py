import json
from pathlib import Path

import pandas as pd
from unidecode import unidecode

from app.domain.exceptions import JugadorNoEncontrado, TemporadaNoEncontrada
from app.domain.posiciones import posicion_corta_es, posicion_detallada_es


def _normalizar(texto: object) -> str:
    return unidecode(str(texto)).lower().strip()


class DatasetRepository:
    """Carga data/processed/dataset.parquet una sola vez y resuelve consultas por jugador."""

    def __init__(self, dataset_path: Path, imagenes_path: Path | None = None):
        df = pd.read_parquet(dataset_path)
        df["saison_id"] = df["saison_id"].astype(int)
        df["_nombre_norm"] = df["Player"].map(_normalizar)

        # Traducción de posiciones a español (solo de presentación: el pipeline de
        # modelado usa las dummies pos_* ya precomputadas, nunca este texto).
        df["posicion_tm"] = df["posicion_tm"].map(posicion_detallada_es)
        df["Pos"] = df["Pos"].map(posicion_corta_es)

        imagenes: dict[str, dict[str, str | None]] = {}
        if imagenes_path is not None and imagenes_path.exists():
            imagenes = json.loads(imagenes_path.read_text(encoding="utf-8"))
        df["foto_url"] = df["player_id"].map(lambda pid: (imagenes.get(pid) or {}).get("foto_url"))
        df["bandera_url"] = df["player_id"].map(lambda pid: (imagenes.get(pid) or {}).get("bandera_url"))
        df["escudo_url"] = df["player_id"].map(lambda pid: (imagenes.get(pid) or {}).get("escudo_url"))

        # Un jugador solo cuenta como vigente si tiene fila en la temporada MÁS RECIENTE
        # del dataset -- si no, es que ya no juega en las 5 grandes ligas (ej. Messi:
        # última fila 2022-2023 con el PSG, se fue a la MLS después). Se descartan TODAS
        # sus filas, no solo la búsqueda, para que tampoco sea alcanzable por ID directo
        # vía /estadisticas, /historial, etc.
        temporada_mas_reciente = df["saison_id"].max()
        jugadores_vigentes = df.loc[df["saison_id"] == temporada_mas_reciente, "player_id"].unique()
        df = df[df["player_id"].isin(jugadores_vigentes)].reset_index(drop=True)

        self._df = df

        self._ultima_temporada = (
            df.sort_values("saison_id").groupby("player_id", as_index=False).tail(1).set_index("player_id")
        )

    def jugadores_vigentes(self) -> pd.DataFrame:
        """Una fila por jugador vigente (su temporada más reciente), indexada por player_id."""
        return self._ultima_temporada

    def resumen(self) -> dict[str, object]:
        """Cifras agregadas del dataset (pantalla de bienvenida). Se calculan sobre `self._df`,
        ya filtrado a jugadores vigentes -- son las mismas cifras que respalda el resto de la API,
        no el dataset crudo sin filtrar."""
        temporadas = sorted(self._df["Season"].unique().tolist())
        temporada_mas_reciente = self._df["saison_id"].max()
        equipos_actuales = self._df.loc[self._df["saison_id"] == temporada_mas_reciente, "Squad"].nunique()
        return {
            "temporada_inicio": temporadas[0],
            "temporada_fin": temporadas[-1],
            "total_temporadas": len(temporadas),
            "ligas": sorted(self._df["Comp"].unique().tolist()),
            "total_jugadores": len(self._ultima_temporada),
            "total_equipos": int(equipos_actuales),
        }

    def buscar(self, query: str, limit: int = 20) -> pd.DataFrame:
        q = _normalizar(query)
        vista = self._ultima_temporada
        mask = vista["_nombre_norm"].str.contains(q, na=False, regex=False)
        return vista.loc[mask].sort_values("Player").head(limit)

    def temporadas_de(self, player_id: str) -> list[int]:
        return sorted(self._df.loc[self._df["player_id"] == player_id, "saison_id"].unique().tolist())

    def obtener_fila(self, player_id: str, saison_id: int | None = None) -> pd.Series:
        temporadas = self.temporadas_de(player_id)
        if not temporadas:
            raise JugadorNoEncontrado(player_id)

        if saison_id is None:
            saison_id = max(temporadas)
        elif saison_id not in temporadas:
            raise TemporadaNoEncontrada(player_id, saison_id)

        fila = self._df[(self._df["player_id"] == player_id) & (self._df["saison_id"] == saison_id)]
        return fila.iloc[0]

    def historial_de(self, player_id: str) -> pd.DataFrame:
        """Una fila por temporada disponible del jugador, ordenadas cronológicamente."""
        if not self.temporadas_de(player_id):
            raise JugadorNoEncontrado(player_id)
        filas = self._df[self._df["player_id"] == player_id]
        return filas.sort_values("saison_id")
