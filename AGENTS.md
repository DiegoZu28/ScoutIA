# AGENTS.md — ScoutIA

Convenciones, decisiones y trampas del proyecto. Actualizar al cerrar cada fase (regla del
documento de arranque de ScoutIA).

## Dos mundos de Python en este repo

- **Raíz** (`requirements.txt`, pip, `.venv`/`.venv312`, `notebooks/`, `scripts/`, `src/`):
  el lado de ciencia de datos — scraping, EDA, ingeniería de variables, modelado, y ahora
  `scripts/build_model_artifacts.py`, que congela el modelo elegido en `models/` y produce
  `data/processed/dataset.parquet`. Se corre con `.venv312` (tiene xgboost/shap/sklearn en
  las versiones correctas).
- **`app/`**: proyecto `uv` independiente (`app/pyproject.toml`, layout `src/`), el backend
  FastAPI de ScoutIA. Tiene su propio `.venv` (`app/.venv`), separado del de la raíz a
  propósito — evita que `uv sync` colisione con el `.venv` de pip que ya existía en la raíz.
- **`frontend/`**: workspace Angular 22 (standalone) + Tailwind v4. Node se instaló vía
  `nvm` (usuario, sin sudo) — hay que sourcearlo en cada shell nueva:
  `export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"`.

No mezclar estos tres mundos (no instalar paquetes de FastAPI en `.venv312`, no correr
notebooks con el venv de `app/`, etc.).

## Reglas no negociables del producto (spec de ScoutIA)

- El valor de mercado **siempre se presenta como banda** (`valor_bajo`/`valor_medio`/`valor_alto`),
  nunca como cifra puntual.
- Nunca lenguaje de "comprar/vender" — los residuales (Fase futura, Oportunidades) se
  presentan como "casos a revisión manual".
- El LLM (a partir de Fase 2) **nunca calcula un número** — solo verbaliza el JSON que le
  entregan los agentes. Todo el texto que ya genera el backend (ej. `metodologia_nota` en
  `PrediccionValor`) está escrito pensando en que eventualmente lo lea un LLM sin que tenga
  que inventar nada.

## Cómo regenerar los artefactos (`models/` + `dataset.parquet`)

```
.venv312/bin/python scripts/build_model_artifacts.py
```

Lee `data/processed/fbref_tm_features.parquet` y `fbref_tm_eda.parquet`, reentrena
TargetEncoder+XGBoost sobre el 100% de los datos (mismos hiperparámetros ya elegidos en
`04-modelado.ipynb`, sin retunear), agrega SHAP/percentiles/KMeans (trabajo nuevo, no
existía en ninguna notebook), y escribe:
- `models/*.joblib` (encoder, modelo, feature_cols, shap explainer, kmeans, cluster_labels)
- `models/metadata.json` (hiperparámetros, métricas de test documentadas, config de percentiles/clustering)
- `data/processed/dataset.parquet` (panel jugador-temporada listo para servir)

**Invariante crítico del join:** `fbref_tm_eda.parquet` tiene 735 grupos `(player_id, saison_id)`
duplicados por transferencias a media temporada (mismo bug ya conocido, ver commit "Cruce
FBref y Transfermarkt"). El script reaplica exactamente la regla de `club_coincide` de
`03-ingenieria_variables.ipynb` (celda 8) y **hace `assert` de que las keys resultantes
coinciden 1:1 con `fbref_tm_features.parquet`** — si алгún día cambian los datos fuente y el
assert revienta, es la señal de que hay que revisar esa regla, no de saltársela.

Las etiquetas de arquetipo (`CLUSTER_LABELS` en el script) se escribieron a mano tras leer
el perfil crudo por cluster que imprime el script. Perfil actual (k=5):

| cluster | n | edad | minutos | goles | asist. | tiros | amarillas | PPM equipo | etiqueta |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 2490 | 23.69 | 572 | 0.38 | 0.37 | 4.59 | 0.95 | 2.07 | Rotación joven en clubes de alto rendimiento |
| 1 | 1901 | 25.52 | 1962 | 4.91 | 3.55 | 40.48 | 3.69 | 1.49 | Titular ofensivo de buen nivel |
| 2 | 513 | 26.21 | 2395 | 13.51 | 5.03 | 76.67 | 3.89 | 1.67 | Estrella ofensiva de máximo volumen |
| 3 | 3774 | 23.66 | 476 | 0.26 | 0.21 | 4.30 | 0.90 | 0.72 | Joven de plantilla modesta, poca participación |
| 4 | 4344 | 27.08 | 1940 | 1.06 | 1.15 | 15.23 | 4.60 | 1.31 | Titular recurrente, perfil de contención |

Si se vuelve a correr el script con datos distintos, los `cluster_id` de KMeans pueden salir
en otro orden — releer el perfil impreso antes de confiar en las etiquetas.

**Decisión importante (explorada en `notebooks/06-perfil.ipynb`):** las 3 variables ofensivas
(`Performance_Gls/Ast_rs`, `Standard_Sh_rs`) que usa el modelo de valor están relativizadas
por posición desde `03-ingenieria_variables.ipynb` (correcto ahí: "¿rindió bien para su
rol?"). Para el **clustering de arquetipo** eso es contraproducente -- aplana la diferencia
real entre un delantero goleador y un defensa que mete algunos goles inusuales para su
posición (ej. Haaland con 22-36 goles reales termina con un `Gls_rs` similar o menor al de
Van Dijk con 3 goles). Probado empíricamente: con las variables por posición ningún cluster
superaba 30% de concentración en una sola posición; en escala global aparece un cluster
57% `Centre-Forward` (el de "Estrella ofensiva", arriba). Por eso `fit_archetype_kmeans()`
recalcula esas 3 variables en escala **global** (`CLUSTER_COLS`, con sufijo `_rs_global`)
solo para el clustering, sin tocar `feature_cols` que usa el modelo de valor -- son dos
preguntas distintas ("¿es bueno para su rol?" vs. "¿juega parecido a quién?") que necesitan
escalas distintas del mismo dato.

**Trampa encontrada:** `Performance_TklW`/`Performance_Int` dejaron de existir en
`fbref_tm_features.parquet` cuando `03-ingenieria_variables.ipynb` empezó a escalarlas por
posición (mismo cambio de arriba). El script no se había vuelto a correr desde ese cambio, y
`build_dataset()` las esperaba crudas para el endpoint `/percentiles` del backend -- rompía
en silencio (los tests de `app/tests/` lo agarraron). Ahora se traen explícitamente de
`fbref_tm_eda.parquet` en `raw_stats_cols`, igual que el resto de las estadísticas crudas.
Si en el futuro se agregan más columnas `_rs por posición` en `03`, revisar si
`build_dataset()` necesita el mismo tratamiento.

## Versiones que deben mantenerse sincronizadas

`.venv312` (raíz, `requirements.txt`) y `app/pyproject.toml` deben tener las **mismas
versiones exactas** de `pandas`, `pyarrow`, `numpy`, `scikit-learn`, `xgboost`, `shap`,
`joblib` — los `.joblib` en `models/` se picklean con las versiones de `.venv312`, y un
desajuste puede romper la deserialización en `app/` (silenciosa o ruidosamente). Al
actualizar una de estas librerías en un lado, actualizar el otro.

## Decisiones de diseño de la Fase 1 (revisables, no dogma)

1. El modelo servido se reentrena sobre el 100% de los datos (no solo train) — las métricas
   de test de `04-modelado.ipynb` (R²=0.8276, RMSE log10=0.2607) quedan documentadas en
   `models/metadata.json` como la estimación honesta de generalización, no como el
   desempeño exacto del modelo servido.
2. Percentiles calculados sobre 8 estadísticas (ver `PERCENTILE_STATS` en el script),
   agrupando por `posicion_tm` + `Season`.
3. KMeans con k=5 (silhouette mejor en k=3, pero muy tosco como feature de producto).
4. Banda de valor = `10**(pred_log ± 1×RMSE_test(log10))` — proxy pragmático, no un
   intervalo estadístico riguroso.
5. SHAP se muestra en espacio log10 (magnitud + dirección), nunca convertido a euros por
   variable — convertir sería matemáticamente engañoso.
6. Endpoint extra `GET /{player_id}/ficha` (no está en la lista de tools del spec): combina
   los 4 endpoints granulares en una sola llamada, solo por conveniencia del frontend. Los 4
   granulares (`estadisticas`, `valor`, `percentiles`, `arquetipo`) siguen siendo la fuente
   de verdad para cuando la Fase 2 los use como tools de agentes.
7. Frontend: `HttpClient` + señales (`signal`/`effect`) para el estado de carga, no la API
   `resource()` nueva de Angular ni RxJS+`async` pipe puro — se prefirió por simplicidad y
   robustez frente a *type narrowing* de uniones discriminadas en templates (este proyecto
   no tiene `strict`/`strictTemplates` activado en `tsconfig.json`).
8. Radar de percentiles: SVG hecho a mano en `viz/radar-chart/`, sin librería de charts.

## Trampas encontradas

- **nvm no persiste entre invocaciones de shell no interactivas** — siempre sourcear
  `export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"` al inicio de cualquier comando que use
  `node`/`npm`/`ng`/`npx`.
- **`openapi-typescript` tiene un peer-dependency desactualizado** (pide `typescript@^5.x`,
  el proyecto usa `~6.0.2`) — se instaló con `--legacy-peer-deps`. Funciona bien en la
  práctica.
- Al deserializar los `.joblib` aparecen muchos `DeprecationWarning` de numpy
  (`array.shape = ...` deprecado en numpy 2.5, viene de dentro de `joblib.numpy_pickle`).
  No rompe nada todavía, pero si numpy sube de major version puede dejar de funcionar —
  vigilar al actualizar numpy.
- El merge `fbref_tm_eda.parquet` ↔ `fbref_tm_features.parquet` **no es un merge trivial**
  por los 735 grupos duplicados — ver la sección de arriba antes de tocar el script.

## Comandos

```bash
# Regenerar artefactos (datos/modelo)
.venv312/bin/python scripts/build_model_artifacts.py

# Backend
cd app && uv sync && uv run uvicorn app.main:app --reload --port 8000
cd app && uv run pytest -q

# Frontend
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"
cd frontend && npm start                       # http://localhost:4200
cd frontend && npm run generate:api-types       # regenerar tipos desde /openapi.json (requiere backend corriendo)
```

## Qué queda explícitamente fuera de la Fase 1 (diferido a Fase 2+)

Orquestador de agentes de OpenAI (`agents/`, `tools/` en `app/` — ni siquiera se crearon
como carpetas vacías), Chat, CriticAgent con validación por regex, vista Comparador, vista
Oportunidades, vista Trazabilidad, red neuronal, selector de temporada en el frontend.
Autenticación/base de datos/Docker están explícitamente prohibidos por el spec de ScoutIA
en cualquier fase.
