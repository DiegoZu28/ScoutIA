from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.api.v1.jugadores import router as jugadores_router
from app.core.config import REPO_ROOT, get_settings
from app.domain.dataset_repository import DatasetRepository
from app.narrativa.generador import NarradorComparacion
from app.valuation.predictor import Predictor

FRONTEND_DIST = REPO_ROOT / "frontend" / "dist" / "frontend" / "browser"


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.dataset_repository = DatasetRepository(settings.dataset_path, settings.imagenes_path)
    app.state.predictor = Predictor(settings.models_dir)
    app.state.narrador = (
        NarradorComparacion(api_key=settings.openai_api_key, modelo=settings.llm_modelo)
        if settings.openai_api_key
        else None
    )
    yield


app = FastAPI(title="ScoutIA API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=get_settings().cors_origins,
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(jugadores_router, prefix="/api/v1")

if FRONTEND_DIST.is_dir():
    # Sirve el build de Angular (`cd frontend && npm run build`) desde el mismo origen que
    # la API, para compartir la app con una sola URL/puerto (LAN o túnel) sin CORS ni hosts
    # hardcodeados. El catch-all cae a index.html para las rutas del router de Angular
    # (ej. /oportunidades) que no son un archivo real del build.
    @app.get("/{full_path:path}", include_in_schema=False)
    def servir_frontend(full_path: str) -> FileResponse:
        candidato = FRONTEND_DIST / full_path
        if full_path and candidato.is_file():
            return FileResponse(candidato)
        return FileResponse(FRONTEND_DIST / "index.html")
