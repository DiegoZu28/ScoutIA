from pathlib import Path

import pandas as pd
from unidecode import unidecode

from app.domain.exceptions import JugadorNoEncontrado, TemporadaNoEncontrada


def _normalizar(texto: object) -> str:
    return unidecode(str(texto)).lower().strip()


class DatasetRepository:
    """Carga data/processed/dataset.parquet una sola vez y resuelve consultas por jugador."""

    def __init__(self, dataset_path: Path):
        df = pd.read_parquet(dataset_path)
        df["saison_id"] = df["saison_id"].astype(int)
        df["_nombre_norm"] = df["Player"].map(_normalizar)

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
