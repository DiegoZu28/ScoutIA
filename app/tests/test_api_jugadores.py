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
