import json
from pathlib import Path

import joblib
import pandas as pd

from app.domain.feature_labels import etiqueta_legible


class Predictor:
    """Carga Lasso + scaler una sola vez y sirve predicciones por fila.

    La contribución de cada variable es exacta, no una aproximación: para un modelo
    lineal, contribución_i = coeficiente_i × valor_estandarizado_i, y la suma de todas
    las contribuciones + el intercepto reconstruye la predicción exacta en espacio log10.
    """

    def __init__(self, models_dir: Path):
        self._model = joblib.load(models_dir / "lasso_model.joblib")
        self._scaler = joblib.load(models_dir / "scaler.joblib")
        self._feature_cols: list[str] = joblib.load(models_dir / "feature_cols.joblib")

        metadata = json.loads((models_dir / "metadata.json").read_text())
        self._rmse_log10: float = metadata["test_metrics_notebook_04"]["rmse_log10"]

    def _fila_a_x_escalado(self, fila: pd.Series):
        x = fila[self._feature_cols].to_frame().T.astype(float)
        return self._scaler.transform(x)[0]

    def predecir_banda(self, fila: pd.Series) -> dict:
        x_escalado = self._fila_a_x_escalado(fila)
        pred_log = float(self._model.predict(x_escalado.reshape(1, -1))[0])
        return {
            "valor_bajo": 10 ** (pred_log - self._rmse_log10),
            "valor_medio": 10**pred_log,
            "valor_alto": 10 ** (pred_log + self._rmse_log10),
            "moneda": "EUR",
        }

    def explicar(self, fila: pd.Series, top_n: int = 8) -> list[dict]:
        x_escalado = self._fila_a_x_escalado(fila)
        contribuciones_todas = self._model.coef_ * x_escalado

        contribuciones = sorted(
            zip(self._feature_cols, contribuciones_todas),
            key=lambda par: abs(par[1]),
            reverse=True,
        )[:top_n]

        return [
            {
                "feature": feature,
                "etiqueta": etiqueta_legible(feature),
                "contribucion_log": float(contribucion),
                "valor_bruto_jugador": float(fila[feature]),
                "direccion": "sube" if contribucion > 0 else "baja",
            }
            for feature, contribucion in contribuciones
            if contribucion != 0  # Lasso lleva varios coeficientes exactamente a cero
        ]
