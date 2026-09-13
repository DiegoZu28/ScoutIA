class JugadorNoEncontrado(Exception):
    def __init__(self, player_id: str):
        self.player_id = player_id
        super().__init__(f"No se encontró el jugador '{player_id}'")


class TemporadaNoEncontrada(Exception):
    def __init__(self, player_id: str, saison_id: int):
        self.player_id = player_id
        self.saison_id = saison_id
        super().__init__(f"El jugador '{player_id}' no tiene datos para la temporada {saison_id}")
