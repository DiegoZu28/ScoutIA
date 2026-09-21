import pytest


def test_oportunidades_devuelve_candidatos_ordenados_por_brecha(client):
    resp = client.get("/api/v1/jugadores/oportunidades", params={"limit": 10})
    assert resp.status_code == 200
    data = resp.json()

    jugadores = data["jugadores"]
    assert 0 < len(jugadores) <= 10

    diferencias = [j["diferencia_eur"] for j in jugadores]
    assert diferencias == sorted(diferencias, reverse=True)

    for j in jugadores:
        banda = j["banda"]
        assert banda["valor_bajo"] < banda["valor_medio"] < banda["valor_alto"]
        assert banda["valor_medio"] > j["valor_mercado_eur"]
        assert j["diferencia_eur"] == pytest.approx(banda["valor_medio"] - j["valor_mercado_eur"])
        assert j["diferencia_pct"] == pytest.approx(j["diferencia_eur"] / j["valor_mercado_eur"])
        assert j["banda_completa_por_encima"] == (banda["valor_bajo"] > j["valor_mercado_eur"])


def test_oportunidades_respeta_limit(client):
    resp = client.get("/api/v1/jugadores/oportunidades", params={"limit": 3})
    assert resp.status_code == 200
    assert len(resp.json()["jugadores"]) == 3


def test_oportunidades_nunca_usa_lenguaje_de_compra_o_venta(client):
    resp = client.get("/api/v1/jugadores/oportunidades")
    assert resp.status_code == 200
    nota = resp.json()["metodologia_nota"].lower()
    assert "comprar" not in nota
    assert "vender" not in nota
    assert "revisión manual" in nota
