import pytest

MBAPPE_ID = "342229"
HAALAND_ID = "418560"


def test_buscar_jugador_encuentra_mbappe(client):
    resp = client.get("/api/v1/jugadores/buscar", params={"q": "mbapp"})
    assert resp.status_code == 200
    nombres = [j["nombre"] for j in resp.json()]
    assert "Kylian Mbappé" in nombres


def test_buscar_jugador_normaliza_acentos(client):
    resp = client.get("/api/v1/jugadores/buscar", params={"q": "haaland"})
    assert resp.status_code == 200
    assert any(j["player_id"] == HAALAND_ID for j in resp.json())


def test_estadisticas_cambian_de_club_por_temporada(client):
    r_2021 = client.get(f"/api/v1/jugadores/{MBAPPE_ID}/estadisticas", params={"temporada": 2021})
    r_2025 = client.get(f"/api/v1/jugadores/{MBAPPE_ID}/estadisticas", params={"temporada": 2025})
    assert r_2021.status_code == 200
    assert r_2025.status_code == 200
    assert r_2021.json()["club"] == "PSG"
    assert r_2025.json()["club"] == "Real Madrid"


def test_estadisticas_traen_contrato_y_liga(client):
    resp = client.get(f"/api/v1/jugadores/{HAALAND_ID}/estadisticas")
    assert resp.status_code == 200
    data = resp.json()
    assert "contrato_conocido" in data
    assert "dias_contrato_restante" in data
    assert isinstance(data["gano_liga"], bool)
    assert isinstance(data["gano_champions"], bool)


def test_valor_devuelve_banda_ordenada_con_contribuciones(client):
    resp = client.get(f"/api/v1/jugadores/{HAALAND_ID}/valor")
    assert resp.status_code == 200
    data = resp.json()
    banda = data["banda"]
    assert banda["valor_bajo"] < banda["valor_medio"] < banda["valor_alto"]
    assert 0 < len(data["contribuciones"]) <= 8
    assert "XGBoost" not in data["metodologia_nota"]
    assert "Lasso" not in data["metodologia_nota"]


def test_percentiles_y_arquetipo_responden(client):
    r_pctl = client.get(f"/api/v1/jugadores/{HAALAND_ID}/percentiles")
    r_arq = client.get(f"/api/v1/jugadores/{HAALAND_ID}/arquetipo")
    assert r_pctl.status_code == 200
    assert r_arq.status_code == 200
    assert len(r_pctl.json()["percentiles"]) == 8
    assert r_arq.json()["etiqueta"]


def test_historial_trae_una_fila_por_temporada(client):
    resp = client.get(f"/api/v1/jugadores/{HAALAND_ID}/historial")
    assert resp.status_code == 200
    data = resp.json()
    assert data["nombre"] == "Erling Haaland"
    assert len(data["temporadas"]) >= 2
    saison_ids = [t["saison_id"] for t in data["temporadas"]]
    assert saison_ids == sorted(saison_ids)


def test_jugador_inexistente_devuelve_404(client):
    resp = client.get("/api/v1/jugadores/no-existe-123/estadisticas")
    assert resp.status_code == 404


def test_ficha_combina_los_cinco_endpoints(client):
    resp = client.get(f"/api/v1/jugadores/{MBAPPE_ID}/ficha")
    assert resp.status_code == 200
    data = resp.json()
    assert {"estadisticas", "valor", "percentiles", "arquetipo", "historial"} == set(data.keys())


def test_comparar_devuelve_ambos_jugadores_y_diferencias(client):
    resp = client.get(
        "/api/v1/jugadores/comparar",
        params={"jugador_a": MBAPPE_ID, "jugador_b": HAALAND_ID},
    )
    assert resp.status_code == 200
    data = resp.json()

    assert data["jugador_a"]["player_id"] == MBAPPE_ID
    assert data["jugador_b"]["player_id"] == HAALAND_ID

    assert len(data["percentiles"]) == 8
    for fila in data["percentiles"]:
        assert fila["diferencia"] == pytest.approx(fila["percentil_a"] - fila["percentil_b"])

    valor = data["valor"]
    assert valor["banda_a"]["valor_bajo"] < valor["banda_a"]["valor_medio"] < valor["banda_a"]["valor_alto"]
    assert valor["diferencia_valor_medio_eur"] == pytest.approx(
        valor["banda_a"]["valor_medio"] - valor["banda_b"]["valor_medio"]
    )
    assert 0 < len(valor["contribuciones_diferencia"]) <= 8
    for c in valor["contribuciones_diferencia"]:
        assert c["diferencia_log"] == pytest.approx(c["contribucion_log_a"] - c["contribucion_log_b"])

    arquetipo = data["arquetipo"]
    assert arquetipo["mismo_arquetipo"] == (arquetipo["cluster_id_a"] == arquetipo["cluster_id_b"])


def test_comparar_respeta_temporada_por_jugador(client):
    resp = client.get(
        "/api/v1/jugadores/comparar",
        params={"jugador_a": MBAPPE_ID, "jugador_b": MBAPPE_ID, "temporada_a": 2021, "temporada_b": 2025},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["jugador_a"]["club"] == "PSG"
    assert data["jugador_b"]["club"] == "Real Madrid"


def test_comparar_con_jugador_inexistente_devuelve_404(client):
    resp = client.get(
        "/api/v1/jugadores/comparar",
        params={"jugador_a": MBAPPE_ID, "jugador_b": "no-existe-123"},
    )
    assert resp.status_code == 404


class _NarradorFalso:
    """Sustituye al narrador real en tests: no llama a OpenAI ni gasta cuota."""

    def __init__(self):
        self.comparacion_recibida = None

    def redactar(self, comparacion):
        self.comparacion_recibida = comparacion
        return {
            "resumen": "Resumen de prueba.",
            "fortalezas_jugador_a": ["Mejor en X"],
            "fortalezas_jugador_b": ["Mejor en Y"],
            "explicacion_diferencia_valor": "La diferencia se explica por Z.",
        }


def test_comparar_narrativa_usa_el_narrador_configurado(client):
    narrador_falso = _NarradorFalso()
    client.app.state.narrador = narrador_falso

    resp = client.get(
        "/api/v1/jugadores/comparar/narrativa",
        params={"jugador_a": MBAPPE_ID, "jugador_b": HAALAND_ID},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["resumen"] == "Resumen de prueba."
    assert data["fortalezas_jugador_a"] == ["Mejor en X"]
    assert data["fortalezas_jugador_b"] == ["Mejor en Y"]
    assert data["explicacion_diferencia_valor"] == "La diferencia se explica por Z."
    assert narrador_falso.comparacion_recibida.jugador_a.player_id == MBAPPE_ID
    assert narrador_falso.comparacion_recibida.jugador_b.player_id == HAALAND_ID


def test_comparar_narrativa_sin_narrador_devuelve_503(client):
    client.app.state.narrador = None
    resp = client.get(
        "/api/v1/jugadores/comparar/narrativa",
        params={"jugador_a": MBAPPE_ID, "jugador_b": HAALAND_ID},
    )
    assert resp.status_code == 503
