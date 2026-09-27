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
TargetEncoder+Lasso (`LassoCV`) sobre el 100% de los datos -- **no** XGBoost: XGBoost daba
mejores métricas en `04-modelado.ipynb` (R²≈0.83 vs. 0.73 del Lasso) pero se descartó para
el modelo servido a propósito, porque los coeficientes lineales dan una contribución exacta
y aditiva por variable (coeficiente × valor estandarizado, sin aproximar vía SHAP sobre un
ensemble de árboles) -- más alineado con el pedido del profesor de usar métodos clásicos, no
ensembles (ver docstring de `scripts/build_model_artifacts.py`). Agrega percentiles/KMeans
(trabajo nuevo, no existía en ninguna notebook), y escribe:
- `models/*.joblib` (target encoder, scaler, modelo Lasso, feature_cols, kmeans, cluster_labels)
- `models/metadata.json` (hiperparámetros, métricas de test documentadas, config de percentiles/clustering)
- `data/processed/dataset.parquet` (panel jugador-temporada listo para servir)

**Invariante crítico del join:** `fbref_tm_eda.parquet` tiene 735 grupos `(player_id, saison_id)`
ambiguos (más de un `Squad` distinto para la misma temporada) — dos causas distintas mezcladas
ahí: colisiones de nombre en el cruce FBref↔Transfermarkt (bug real, ver commit "Cruce FBref y
Transfermarkt") y jugadores cedidos (misma persona, dos clubes legítimos en la misma
temporada). El script reaplica exactamente la regla de `03-ingenieria_variables.ipynb`
(celda 8), que ahora es de dos niveles:

1. Si hay evidencia de cesión en `data/interim/prestamos.csv` (generado por
   `scripts/detectar_prestamos.py` a partir de las insignias "On loan from X" / "Returned
   after loan spell with X" de las plantillas de Transfermarkt) para ese `(player_id,
   saison_id)`, se conserva la fila del club donde jugó de verdad, no la del club dueño.
2. Si no, la regla original por `club_coincide`: se conserva la única fila que coincide con
   el club de Transfermarkt; si ninguna o más de una coincide, se descarta el grupo entero.

Desglose actual: 58 grupos resueltos vía evidencia de cesión (23 en la temporada
2025-2026), 603 vía `club_coincide`, 74 sin fila confiable (descartados). Caso que motivó el
punto 1: Endrick, cedido en Olympique Lyon toda 2025-2026 (16 partidos, 5 goles) — antes
`club_coincide` se quedaba con sus 12 minutos post-regreso a Real Madrid; ver memoria
`data_quality_loan_split_bug`.

El script **hace `assert` de que las keys resultantes coinciden 1:1 con
`fbref_tm_features.parquet`** — si algún día cambian los datos fuente (o se vuelve a correr
`03-ingenieria_variables.ipynb`) y el assert revienta, es la señal de que hay que revisar
esa regla, no de saltársela.

**Bug residual conocido, no arreglado:** ni `club_coincide` ni la evidencia de cesión
atrapan el caso donde el `player_id` está mal cruzado con una persona real distinta *y esa
persona equivocada* también coincide con su propio club de Transfermarkt — ver memoria
`data_quality_rodri_merge_bug` (casos concretos: Marc Guéhi y Antoine Semenyo, ambos
muestran "Manchester City" en 2025-2026 de forma espuria).

Las etiquetas de arquetipo (`CLUSTER_LABELS` en el script) se escribieron a mano tras leer
el perfil crudo por cluster que imprime el script. Perfil actual (k=5):

| cluster | n | edad | minutos | goles | asist. | tiros | amarillas | PPM equipo | etiqueta |
|---|---|---|---|---|---|---|---|---|---|
| 0 | 3803 | 23.71 | 482 | 0.25 | 0.21 | 4.32 | 0.91 | 0.72 | Joven de plantilla modesta, poca participación |
| 1 | 4328 | 27.01 | 1944 | 1.09 | 1.17 | 15.49 | 4.62 | 1.31 | Titular recurrente, perfil de contención |
| 2 | 499 | 26.18 | 2395 | 13.66 | 4.94 | 76.95 | 3.88 | 1.66 | Estrella ofensiva de máximo volumen |
| 3 | 1872 | 25.56 | 1969 | 4.98 | 3.61 | 40.97 | 3.71 | 1.49 | Titular ofensivo de buen nivel |
| 4 | 2521 | 23.77 | 589 | 0.39 | 0.37 | 4.65 | 0.96 | 2.07 | Rotación joven en clubes de alto rendimiento |

(Perfil de la corrida más reciente, post-fix de cesiones — 2026-09-18. El orden de
`cluster_id` cambió respecto a la tabla anterior por el mismo motivo que advierte el párrafo
de abajo: **siempre releer el perfil impreso antes de confiar en `CLUSTER_LABELS`**, no
asumir que el índice se mantiene entre corridas.)

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
versiones exactas** de `pandas`, `pyarrow`, `numpy`, `scikit-learn`, `joblib` — los `.joblib`
en `models/` se picklean con las versiones de `.venv312`, y un desajuste puede romper la
deserialización en `app/` (silenciosa o ruidosamente). Al actualizar una de estas librerías
en un lado, actualizar el otro. `xgboost`/`shap` **no** están en esta lista a propósito:
`.venv312` los sigue necesitando (`04-modelado.ipynb` compara Lasso contra XGBoost), pero se
quitaron de `app/pyproject.toml` -- el backend nunca los importa (el modelo servido es Lasso,
ver más abajo), y arrastraban una cadena de dependencias pesada (`numba`, `llvmlite`,
`nvidia-nccl-cu13`, ~9 paquetes) sin ningún uso real, un problema real para el tamaño del
deploy en Vercel (ver sección de despliegue en el `README.md`).

## Decisiones de diseño de la Fase 1 (revisables, no dogma)

1. El modelo servido es **Lasso**, no XGBoost (que daba mejores métricas, R²≈0.83) — se
   eligió por interpretabilidad: coeficientes lineales dan una contribución exacta y aditiva
   por variable, sin aproximar vía SHAP. Se reentrena sobre el 100% de los datos (no solo
   train) — las métricas de test de `04-modelado.ipynb` para este Lasso (R²=0.731312,
   RMSE log10=0.325505, ver `TEST_METRICS_NOTEBOOK_04` en el script) quedan documentadas en
   `models/metadata.json` como la estimación honesta de generalización, no como el
   desempeño exacto del modelo servido.
2. Percentiles calculados sobre 8 estadísticas (ver `PERCENTILE_STATS` en el script),
   agrupando por `posicion_tm` + `Season`.
3. KMeans con k=5 (silhouette mejor en k=3, pero muy tosco como feature de producto).
4. Banda de valor = `10**(pred_log ± 1×RMSE_test(log10))` — proxy pragmático, no un
   intervalo estadístico riguroso.
5. Las contribuciones de valor (`Predictor.explicar`/`explicar_diferencia`) son exactas, no
   una aproximación tipo SHAP: para un modelo lineal, contribución_i = coeficiente_i × valor
   estandarizado_i, y la suma de todas + el intercepto reconstruye la predicción exacta en
   espacio log10. Se muestran en ese mismo espacio log10 (magnitud + dirección), nunca
   convertidas a euros por variable — convertir sería matemáticamente engañoso.
6. Endpoint extra `GET /{player_id}/ficha` (no está en la lista de tools del spec): combina
   los 4 endpoints granulares en una sola llamada, solo por conveniencia del frontend. Los 4
   granulares (`estadisticas`, `valor`, `percentiles`, `arquetipo`) siguen siendo la fuente
   de verdad para cuando la Fase 2 los use como tools de agentes.
7. Frontend: `HttpClient` + señales (`signal`/`effect`) para el estado de carga, no la API
   `resource()` nueva de Angular ni RxJS+`async` pipe puro — se prefirió por simplicidad y
   robustez frente a *type narrowing* de uniones discriminadas en templates (este proyecto
   no tiene `strict`/`strictTemplates` activado en `tsconfig.json`).
8. Radar de percentiles: SVG hecho a mano en `viz/radar-chart/`, sin librería de charts.

## Decisiones de diseño del Comparador + LLM (adelantado desde "fuera de Fase 1", ver abajo)

1. `GET /jugadores/comparar` no llama a un solo modelo nuevo: reutiliza los 3 ya servidos
   (percentiles precalculados, Lasso, KMeans) y solo agrega la resta/alineación entre las
   dos filas. Ningún modelo se reentrena para el comparador.
2. La contribución a la diferencia de valor (`Predictor.explicar_diferencia`) NO es la
   resta de los top-N de `explicar()` de cada jugador por separado (esos top-N pueden no
   compartir features) — se calcula la contribución completa de ambos sobre las mismas
   `feature_cols` y se ordena por la diferencia. Como el modelo es lineal, la suma de todas
   las diferencias reconstruye exactamente la brecha en espacio log10.
3. El LLM (`app/src/app/narrativa/`) solo redacta el JSON de diferencias ya calculado —
   nunca recibe stats crudas ni calcula nada, cumpliendo la regla ya escrita arriba. Mismo
   patrón de `response_format: json_schema` ya validado en el prototipo de noticias con LLM
   (notebook `05-llm.ipynb`, eliminado 2026-09-20 al descartarse esa feature — ver sección
   de descartadas más abajo).
4. **Encontrado probando con la API real:** pasarle al LLM un booleano (`favorece_a`) para
   indicar a qué jugador beneficia cada factor de valor causó una atribución cruzada (le
   asignó un factor al jugador equivocado en la prosa). Se corrigió mandando el nombre del
   jugador ya resuelto (`jugador_favorecido`) en vez del booleano — quitarle al modelo la
   indirección booleano→jugador eliminó el error en las pruebas repetidas.
5. La narrativa es un endpoint separado (`/comparar/narrativa`) que el frontend dispara con
   un botón explícito, no automáticamente al elegir jugadores — la llamada a OpenAI tiene
   costo y puede tardar bastante (variable, ~5–40s de punta a punta contra la API real).
   `app.state.narrador` es `None` si no hay `OPENAI_API_KEY`; el endpoint responde 503.
6. Colores fijos por identidad (jugador A = índigo `#4f46e5`, jugador B = ámbar `#d97706`),
   validados como colorblind-safe con el validador del skill de dataviz, reutilizados en
   radar, tabla de percentiles, barras de valor y arquetipo — nunca se recolorea por rango.
7. `RadarChartComponent` (`viz/radar-chart/`) se generalizó de una serie (`puntos`) a N
   series (`series: SerieRadar[]`) para poder superponer a los dos jugadores; `radar-
   percentiles.component.ts` (ficha individual) ahora le pasa un arreglo de una sola serie,
   sin cambio visual.

## Modo oscuro (2026-09-21)

- Tailwind v4 no trae dark mode por clase activado por defecto (usa `prefers-color-scheme`
  vía media query). Para poder alternarlo manualmente se agregó en `styles.css`:
  `@custom-variant dark (&:where(.dark, .dark *));` — a partir de ahí cualquier `dark:` en
  templates depende de que `<html>` tenga la clase `.dark`, no de la preferencia del SO.
- `core/theme/theme.service.ts` (`ThemeService`, signal `tema: 'claro' | 'oscuro'`) decide el
  tema inicial (localStorage `scoutia-tema` > `prefers-color-scheme` del sistema) y sincroniza
  la clase `.dark` en `<html>` + `localStorage` vía `effect()`. `alternar()` lo invierte. Se
  inyecta una sola vez en `App` (`app.ts`) para garantizar que el `effect` corra desde el
  arranque; el botón sol/luna vive en la navbar (`app.html`).
- `index.html` tiene un script inline en el `<head>` que lee `localStorage`/`matchMedia` y
  aplica `.dark` a `<html>` **antes** de que Angular arranque — sin esto se ve un flash de
  tema claro en cada carga si el usuario ya eligió oscuro.
- Convención de color para dark mode (aplicada a todos los componentes de `frontend/src/app`):
  fondo de página `dark:bg-slate-950`, navbar y tarjetas `dark:bg-slate-900` con
  `dark:border-slate-800`, texto principal `dark:text-slate-100`, texto secundario
  `dark:text-slate-400`. Badges de acento (`bg-indigo-50`/`bg-amber-50`/`bg-red-50` con texto
  `-700`) pasan a `dark:bg-{color}-500/10 dark:text-{color}-400`. Cualquier componente nuevo
  con fondo/texto propio debe seguir esta misma paleta para no romper la consistencia visual.
- Los gráficos SVG (`viz/line-chart/`, `viz/radar-chart/`) tenían líneas de grilla con
  `stroke="#e2e8f0"` fijo en el atributo (no clase) — no reacciona a `dark:`. Se cambió a
  `class="stroke-slate-200 dark:stroke-slate-700"` (Tailwind soporta utilidades `stroke-*`/
  `fill-*` en SVG). Los colores de las líneas de datos (series por jugador, por stat) quedan
  igual en ambos temas a propósito — son colores saturados pensados para contrastar sobre
  cualquier fondo, no se tocan.

## Pantalla de bienvenida y reordenamiento de rutas (2026-09-21)

- `/` dejó de ser la ficha/buscador (`HomeComponent`) y ahora es `BienvenidaComponent`
  (`features/bienvenida/`) — primera vista al entrar a la app y destino del click en el logo
  (`app.html`, `<a routerLink="/">` envolviendo el `<img>`). El buscador+ficha que antes vivía
  en `/` se movió a `/jugador` sin cambios de lógica interna (mismo `HomeComponent`, mismo
  soporte de `?jugador=<id>` como query param).
- Por el movimiento de ruta, `oportunidades.component.html` (el link de cada fila a la ficha
  del jugador) se actualizó de `routerLink="/"` a `routerLink="/jugador"`, manteniendo el
  `queryParams` con el `player_id`. Cualquier otro link nuevo hacia la ficha de un jugador debe
  apuntar a `/jugador`, no a `/`.
- Nav de `app.html` pasó de `Home | Comparador | Oportunidades` a
  `Inicio | Buscar jugador | Comparador | Oportunidades` (`Inicio` → `/`, `Buscar jugador` →
  `/jugador`).
- Las cifras de la bienvenida (temporadas, ligas, jugadores, equipos) **no están hardcodeadas**
  en el frontend — vienen de `GET /api/v1/jugadores/resumen` (`DatasetRepository.resumen()` en
  `app/src/app/domain/dataset_repository.py`), calculadas sobre `self._df` ya filtrado a
  jugadores vigentes (las mismas filas que respaldan el resto de la API). `total_equipos` es
  el conteo de `Squad` únicos solo en la temporada más reciente (96 = 20+20+20+18+18 de las 5
  ligas), no en todo el histórico (que da 130, porque incluye clubes previos de jugadores que
  ya se transfirieron) — la cifra que describe mejor "qué equipos tiene la app hoy".
- Al agregar el endpoint se regeneró `frontend/src/app/core/api/schema.d.ts` con
  `npm run generate:api-types` (requiere el backend corriendo) — cualquier cambio de schema en
  `app/src/app/schemas/` necesita el mismo paso para que el frontend vea los tipos nuevos.

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
- `Settings.model_config.env_file` lee primero el `.env` de la raíz del repo y después
  `app/.env` (que no existe todavía) — así el backend reusa el mismo `OPENAI_API_KEY` que
  ya usaba el prototipo de noticias con LLM (`05-llm.ipynb`, eliminado — ver sección de
  descartadas), sin duplicar el secreto en dos archivos.

## Comandos

```bash
# Regenerar artefactos (datos/modelo)
.venv312/bin/python scripts/build_model_artifacts.py

# Backend
cd app && uv sync && uv run uvicorn app.main:app --reload --port 8000
cd app && uv run pytest -q

# Frontend
export NVM_DIR="$HOME/.nvm"; . "$NVM_DIR/nvm.sh"
cd frontend && npm start                       # http://localhost:4200 (proxy a :8000 vía proxy.conf.json)
cd frontend && npm run generate:api-types       # regenerar tipos desde /openapi.json (requiere backend corriendo)

# Compartir la app (LAN o internet) para que alguien más la pruebe
scripts/compartir_app.sh                        # build de Angular + backend en :8000 (sirve ambos) + túnel público
scripts/detener_app.sh                          # baja todo — a partir de ahí no se gasta nada
```

## Compartir la app con otros (2026-09-19)

`scripts/compartir_app.sh` resuelve "que mis amigos/el profe prueben la app desde otra red"
sin desplegar nada permanente (spec prohíbe Docker en cualquier fase, y esto es para pruebas
puntuales, no para producción):

1. `npm run build` compila Angular a `frontend/dist/frontend/browser/`.
2. `app/src/app/main.py` ahora monta un catch-all (`GET /{full_path:path}`, registrado
   *después* de `include_router` para no pisar `/api/v1/*`) que sirve ese build y cae a
   `index.html` para las rutas del router de Angular (ej. `/oportunidades`) que no son un
   archivo real — así queda **un solo puerto** (8000) sirviendo frontend + API, en vez de
   4200 + 8000 por separado.
3. Por eso `API_BASE_URL` (`frontend/src/app/core/config/api-base-url.ts`) pasó de estar
   hardcodeado a `http://localhost:8000` a ser **relativo** (`/api/v1`) — si no, el navegador
   de un amigo intentaría pegarle a su propio `localhost`, no al servidor real. En dev
   (`npm start`), `proxy.conf.json` reenvía `/api/v1` a `:8000` para que la ruta relativa
   siga funcionando con `ng serve`.
4. El túnel es Cloudflare Tunnel (`cloudflared`, instalado en `~/.local/bin`, sin cuenta —
   "quick tunnel"): URL pública `https://*.trycloudflare.com` distinta cada vez que se corre
   el script, válida mientras el proceso esté vivo.
5. **Costo/exposición:** el LLM (`/comparar/narrativa`) sigue consumiendo `OPENAI_API_KEY`
   por cada llamada real, esté o no la app expuesta — la URL pública es obscura pero no tiene
   auth (prohibida por el spec), así que cualquiera con el link puede llamarlo. Para cero
   riesgo/costo cuando no se está mostrando la app: `scripts/detener_app.sh`.

## Qué queda explícitamente fuera de la Fase 1 (diferido a Fase 2+)

Orquestador de agentes de OpenAI (`agents/`, `tools/` en `app/` — ni siquiera se crearon
como carpetas vacías), CriticAgent con validación por regex, red neuronal, selector de
temporada en el frontend. Autenticación/base de datos/Docker están explícitamente
prohibidos por el spec de ScoutIA en cualquier fase.

**Descartadas (no se van a construir):** Chat y vista Trazabilidad — estaban en el navbar
como placeholders ("Próxima fase") pero se quitaron (2026-09-19) porque se decidió no
implementarlas.

**Notebook `05-llm.ipynb` eliminado (2026-09-20):** era un prototipo (ESPN + OpenAI) para
clasificar noticias por jugador y ligarlas al dataset; se descartó la feature de noticias y
el notebook no tenía ninguna dependencia real — nada en `app/`, `scripts/` ni `frontend/`
lo importaba, y su único output (`data/interim/espn_news/*.parquet`) estaba en
`.gitignore` y no lo leía nada más. No afecta al LLM que sí usa la app
(`app/src/app/narrativa/`, ver decisiones de diseño del Comparador arriba), que es
independiente.

**Vista Comparador:** se adelantó respecto al plan original (ver sección de decisiones de
diseño arriba) — `GET /jugadores/comparar` + `/comparar/narrativa` en el backend, feature
`frontend/src/app/features/comparador/` en el frontend.

**Vista Oportunidades:** también se adelantó (2026-09-19). `GET /jugadores/oportunidades`
(`app/src/app/valuation/oportunidades.py` + `Predictor.predecir_banda_lote`, vectorizado en
vez de llamar `predecir_banda` fila por fila) filtra los ~2545 jugadores vigentes a los que
tienen `valor_medio` (banda del modelo) **por encima** de `valor_eur` (Transfermarkt) —
jugadores que el modelo valora más de lo que refleja su precio de mercado —, ordenados por
brecha absoluta descendente. `banda_completa_por_encima` (incluso el extremo bajo de la banda
ya supera el valor de mercado) es la señal más confiable, mostrada como badge "Señal fuerte"
en el frontend (`frontend/src/app/features/oportunidades/`) — no filtra por ella, solo la
marca. Sigue la regla de bandas + "casos a revisión manual" (nunca comprar/vender) del spec.
El resto de esta lista sigue vigente.
