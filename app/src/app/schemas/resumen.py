from pydantic import BaseModel


class ResumenDataset(BaseModel):
    temporada_inicio: str
    temporada_fin: str
    total_temporadas: int
    ligas: list[str]
    total_jugadores: int
    total_equipos: int
