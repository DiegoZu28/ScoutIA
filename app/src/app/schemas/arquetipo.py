from pydantic import BaseModel


class ArquetipoJugador(BaseModel):
    cluster_id: int
    etiqueta: str
