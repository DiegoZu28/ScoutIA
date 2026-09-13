"""Congela en artefactos servibles el pipeline de valuación validado en 04-modelado.ipynb.

Corre con: .venv312/bin/python scripts/build_model_artifacts.py

Modelo de producción: **Lasso**, no XGBoost -- aunque XGBoost da mejores métricas
(R²=0.83 vs. 0.73), se eligió Lasso a propósito para la app: coeficientes lineales dan
una explicación exacta y aditiva de cada predicción (contribución = coeficiente × valor
estandarizado, sin aproximaciones), más alineado con lo que pide el profesor (métodos
clásicos, no ensembles) que una explicación aproximada vía SHAP sobre un ensemble de
árboles. Reajusta encoder+scaler+Lasso sobre el 100% de fbref_tm_features.parquet (no
solo train) porque el split 80/20 de la notebook era para *medir* generalización, no para
decidir qué ve el modelo que se sirve en producción. Las métricas de test de la notebook
se documentan aparte (TEST_METRICS_NOTEBOOK_04) como la estimación honesta de qué tan bien
generaliza este diseño.

Agrega, como trabajo nuevo (no existía en ninguna notebook): un KMeans de arquetipo, y
percentiles por posición+temporada.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.linear_model import LassoCV
from sklearn.model_selection import KFold
from sklearn.preprocessing import RobustScaler, StandardScaler, TargetEncoder

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "data" / "processed"
MODELS_DIR = ROOT / "models"

ID_COLS = ["Player", "player_id", "saison_id"]
TARGET_COLS = ["valor_eur", "log_valor_eur"]
TARGET = "log_valor_eur"

# Espacio de búsqueda de alpha ya elegido en 04-modelado.ipynb (sección "6. Regularización").
# LassoCV autoajusta el mejor alpha por CV -- no hay un hiperparámetro fijo que congelar
# aparte de este espacio de búsqueda.
LASSO_PARAMS = dict(alphas=100, cv=5, random_state=42, max_iter=20000)

# Métricas de test documentadas en 04-modelado.ipynb (sección "6.2 Comparación final: OLS
# vs. Ridge vs. Lasso"), tal cual las produjo esa corrida — se guardan para Trazabilidad,
# no se recalculan aquí.
TEST_METRICS_NOTEBOOK_04 = {
    "r2_log10": 0.731312,
    "rmse_log10": 0.325505,
    "mae_eur": 4837111.0,
    "mape_pct": 77.729490,
}

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

# Usadas SOLO para el clustering de arquetipo (no para el modelo de valor). Las 3
# ofensivas van en escala global, no por posición -- ver comentario en
# fit_archetype_kmeans() para el porqué (probado en notebooks/06-perfil.ipynb).
CLUSTER_COLS = [
    "Age_rs",
    "altura_m_rs",
    "Playing Time_Min_rs",
    "Performance_Gls_rs_global",
    "Performance_Ast_rs_global",
    "Standard_Sh_rs_global",
    "Performance_CrdY_rs",
    "Team Success_PPM_rs",
]
RAW_OFENSIVAS_CLUSTER = ["Performance_Gls", "Performance_Ast", "Standard_Sh"]

RAW_COLS_FOR_RS = {
    "Age_rs": "Age",
    "altura_m_rs": "altura_m",
    "Playing Time_Min_rs": "Playing Time_Min",
    "Performance_Gls_rs": "Performance_Gls",
    "Performance_Ast_rs": "Performance_Ast",
    "Standard_Sh_rs": "Standard_Sh",
    "Performance_CrdY_rs": "Performance_CrdY",
    "Team Success_PPM_rs": "Team Success_PPM",
}

N_CLUSTERS = 5

# Se completa a mano tras leer el perfil crudo impreso por print_cluster_profile(), luego
# se vuelve a correr el script. Ver AGENTS.md para el perfil que quedó documentado.
CLUSTER_LABELS = {
    0: "Rotación joven en clubes de alto rendimiento",
    1: "Titular ofensivo de buen nivel",
    2: "Estrella ofensiva de máximo volumen",
    3: "Joven de plantilla modesta, poca participación",
    4: "Titular recurrente, perfil de contención",
}


def load_frames():
    df_feat = pd.read_parquet(DATA_DIR / "fbref_tm_features.parquet")
    df_eda = pd.read_parquet(DATA_DIR / "fbref_tm_eda.parquet")
    return df_feat, df_eda


def resolve_eda_ambiguity(df_eda):
    """Reaplica la regla de club_coincide de 03-ingenieria_variables.ipynb (celda 8)."""
    df = df_eda.copy()
    key_cols = ["player_id", "saison_id"]
    n_squads = df.groupby(key_cols)["Squad"].transform("nunique")
    ambiguos = n_squads > 1
    n_true_grupo = df.groupby(key_cols)["club_coincide"].transform("sum")

    n_grupos_ambiguos = df.loc[ambiguos, key_cols].drop_duplicates().shape[0]
    descartar = (ambiguos & (n_true_grupo == 1) & (~df["club_coincide"])) | (
        ambiguos & (n_true_grupo == 0)
    )

    print(f"Grupos (player_id, saison_id) con Squad ambiguo: {n_grupos_ambiguos}")
    print(f"Filas descartadas: {descartar.sum()} de {df.shape[0]}")
    df = df[~descartar].reset_index(drop=True)
    print(f"Shape tras resolver ambigüedad: {df.shape}")
    return df


def assert_join_keys_match(df_eda_resuelto, df_feat):
    key_cols = ["player_id", "saison_id"]
    dup = df_eda_resuelto.duplicated(key_cols).sum()
    assert dup == 0, f"quedaron {dup} filas duplicadas en (player_id, saison_id) tras resolver ambigüedad"

    keys_eda = set(map(tuple, df_eda_resuelto[key_cols].to_numpy()))
    keys_feat = set(map(tuple, df_feat[key_cols].to_numpy()))
    solo_eda = keys_eda - keys_feat
    solo_feat = keys_feat - keys_eda
    assert not solo_eda and not solo_feat, (
        f"las keys no coinciden: {len(solo_eda)} solo en eda-resuelto, {len(solo_feat)} solo en features"
    )
    print("OK: keys (player_id, saison_id) de eda-resuelto == features, sin duplicados\n")


def fit_target_encoder_and_model(df_feat):
    df = df_feat.copy()
    encoder = TargetEncoder(target_type="continuous", cv=KFold(n_splits=5, shuffle=True, random_state=42))
    df["Squad_target_enc"] = encoder.fit_transform(df[["Squad"]], df[TARGET]).ravel()
    df = df.drop(columns=["Squad"])

    feature_cols = [c for c in df.columns if c not in ID_COLS + TARGET_COLS]
    X, y = df[feature_cols], df[TARGET]

    # Lasso (como Ridge) es sensible a la escala -- se estandariza antes de ajustar, igual
    # que en 04-modelado.ipynb. El scaler se guarda: hace falta la misma transformación en
    # cada predicción en producción.
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LassoCV(**LASSO_PARAMS)
    model.fit(X_scaled, y)
    print(f"Lasso final entrenado sobre {X.shape[0]} filas, {len(feature_cols)} features "
          f"(alpha={model.alpha_:.5f})\n")
    return encoder, scaler, model, feature_cols, df


def compute_percentiles(df_eda_resuelto):
    cols = ["player_id", "saison_id", "posicion_tm", "Season"] + PERCENTILE_STATS
    df = df_eda_resuelto[cols].copy()
    grupo = df.groupby(["posicion_tm", "Season"])
    for stat in PERCENTILE_STATS:
        df[f"pctl_{stat}"] = grupo[stat].rank(pct=True)
    df["n_comparacion"] = grupo["posicion_tm"].transform("size")

    pctl_cols = [f"pctl_{s}" for s in PERCENTILE_STATS]
    return df[["player_id", "saison_id", "n_comparacion"] + pctl_cols]


def fit_archetype_kmeans(df_feat, df_eda_resuelto):
    """Performance_Gls_rs/Ast_rs/Sh_rs (en df_feat) están relativizadas por posición --
    correcto para el modelo de valor ("¿rindió bien para su rol?"), pero contraproducente
    para un arquetipo de estilo de juego: aplana la diferencia real entre, por ejemplo,
    un delantero que mete 22-36 goles y un central que mete 3 (inusual para su posición,
    pero un volumen absoluto completamente distinto). Probado en notebooks/06-perfil.ipynb:
    con las variables por posición ningún cluster supera 30% de concentración en una sola
    posición; en escala global aparece un cluster 57% Centre-Forward. Acá se recalculan
    esas 3 en escala global solo para el clustering, sin tocar las columnas que usa el
    modelo de valor.
    """
    ofensivas = df_eda_resuelto[["player_id", "saison_id"] + RAW_OFENSIVAS_CLUSTER]
    cols_base = ["player_id", "saison_id"] + [c for c in CLUSTER_COLS if c in df_feat.columns]
    df_cluster = df_feat[cols_base].merge(ofensivas, on=["player_id", "saison_id"], how="left")
    assert len(df_cluster) == len(df_feat), "el merge no debe cambiar el numero de filas"

    rs_global = RobustScaler().fit_transform(df_cluster[RAW_OFENSIVAS_CLUSTER])
    for i, c in enumerate(RAW_OFENSIVAS_CLUSTER):
        df_cluster[f"{c}_rs_global"] = rs_global[:, i]

    X = df_cluster[CLUSTER_COLS].to_numpy()
    kmeans = KMeans(n_clusters=N_CLUSTERS, random_state=42, n_init=10)
    cluster_id = kmeans.fit_predict(X)
    return kmeans, cluster_id


def print_cluster_profile(df_feat, df_eda_resuelto, cluster_id):
    raw_cols = list(RAW_COLS_FOR_RS.values())
    merged = df_feat[["player_id", "saison_id"]].copy()
    merged["cluster_id"] = cluster_id
    merged = merged.merge(
        df_eda_resuelto[["player_id", "saison_id"] + raw_cols],
        on=["player_id", "saison_id"],
        how="left",
    )
    perfil = merged.groupby("cluster_id")[raw_cols].mean().round(2)
    perfil["n"] = merged.groupby("cluster_id").size()
    print("Perfil crudo por cluster (usar para escribir/ajustar CLUSTER_LABELS a mano):")
    print(perfil.to_string())
    print()
    return perfil


def build_dataset(df_model_full, df_eda_resuelto, percentiles, cluster_id, cluster_labels):
    key_cols = ["player_id", "saison_id"]
    identidad_cols = ["Squad", "Nation", "Pos", "Comp", "Season", "posicion_tm"]
    raw_stats_cols = [
        "Age",
        "altura_m",
        "Playing Time_Min",
        "Performance_Gls",
        "Performance_Ast",
        "Standard_Sh",
        "Performance_CrdY",
        "Team Success_PPM",
        "Performance_Crs",
        # Performance_TklW/Int ya no sobreviven en fbref_tm_features.parquet (03 las
        # reemplazó por su version escalada por posicion) -- se traen crudas de la eda
        # porque el backend las necesita como valor_bruto en /percentiles.
        "Performance_TklW",
        "Performance_Int",
    ]
    # contrato_vence tampoco sobrevive en fbref_tm_features.parquet (03 la eliminó, dejando
    # solo dias_contrato_restante YA IMPUTADO -- ver notebooks/03, seccion 9). Para mostrarle
    # al usuario la fecha real (o "desconocido" si no hay dato, via flag_contrato_conocido,
    # que SI esta en feature_cols) hace falta la version cruda, sin imputar.
    cols_fecha_contrato = ["contrato_vence"]
    eda_slice = (
        df_eda_resuelto[key_cols + identidad_cols + raw_stats_cols + cols_fecha_contrato]
        .drop_duplicates(key_cols)
        .reset_index(drop=True)
    )

    base = df_model_full.copy()
    base["cluster_id"] = cluster_id
    base["cluster_label"] = pd.Series(cluster_id).map(cluster_labels).to_numpy()

    dataset = base.merge(eda_slice, on=key_cols, how="left")
    dataset = dataset.merge(percentiles, on=key_cols, how="left")
    return dataset


def save_artifacts(encoder, scaler, model, feature_cols, kmeans, cluster_labels, dataset):
    MODELS_DIR.mkdir(exist_ok=True)
    joblib.dump(encoder, MODELS_DIR / "target_encoder.joblib")
    joblib.dump(scaler, MODELS_DIR / "scaler.joblib")
    joblib.dump(model, MODELS_DIR / "lasso_model.joblib")
    joblib.dump(feature_cols, MODELS_DIR / "feature_cols.joblib")
    joblib.dump(kmeans, MODELS_DIR / "kmeans_archetype.joblib")
    joblib.dump(cluster_labels, MODELS_DIR / "cluster_labels.joblib")

    # Artefactos del modelo anterior (XGBoost+SHAP) -- ya no se generan, se borran si
    # quedaron de una corrida previa para que nada cargue un modelo viejo por error.
    for obsoleto in ["xgb_model.joblib", "shap_explainer.joblib"]:
        (MODELS_DIR / obsoleto).unlink(missing_ok=True)

    dataset_path = DATA_DIR / "dataset.parquet"
    dataset.to_parquet(dataset_path, index=False)

    metadata = {
        "built_at": datetime.now(timezone.utc).isoformat(),
        "n_rows_dataset": int(len(dataset)),
        "modelo": "Lasso",
        "lasso_alpha": float(model.alpha_),
        "lasso_params_busqueda": LASSO_PARAMS,
        "test_metrics_notebook_04": TEST_METRICS_NOTEBOOK_04,
        "n_clusters": N_CLUSTERS,
        "percentile_stats": PERCENTILE_STATS,
        "rs_cols_for_clustering": CLUSTER_COLS,
    }
    (MODELS_DIR / "metadata.json").write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    print(f"Artefactos guardados en {MODELS_DIR}:")
    for f in sorted(MODELS_DIR.iterdir()):
        print(f"  {f.name}")
    print(f"\n{dataset_path} escrito: {dataset.shape}")


def main():
    df_feat, df_eda = load_frames()
    df_eda_resuelto = resolve_eda_ambiguity(df_eda)
    assert_join_keys_match(df_eda_resuelto, df_feat)

    encoder, scaler, model, feature_cols, df_model_full = fit_target_encoder_and_model(df_feat)
    percentiles = compute_percentiles(df_eda_resuelto)
    kmeans, cluster_id = fit_archetype_kmeans(df_feat, df_eda_resuelto)
    print_cluster_profile(df_feat, df_eda_resuelto, cluster_id)

    dataset = build_dataset(df_model_full, df_eda_resuelto, percentiles, cluster_id, CLUSTER_LABELS)
    save_artifacts(encoder, scaler, model, feature_cols, kmeans, CLUSTER_LABELS, dataset)


if __name__ == "__main__":
    main()
