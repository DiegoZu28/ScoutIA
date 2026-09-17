from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.jugadores import router as jugadores_router
from app.core.config import get_settings
from app.domain.dataset_repository import DatasetRepository
from app.narrativa.generador import NarradorComparacion
from app.valuation.predictor import Predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.dataset_repository = DatasetRepository(settings.dataset_path)
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
