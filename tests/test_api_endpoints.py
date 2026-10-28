"""
Pruebas de integración asíncronas para los API Endpoints de FastAPI y verificación de determinismo (T=0.0).
"""
import pytest
from httpx import AsyncClient, ASGITransport
from backend.main import app
from backend.database import execute_dml

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.mark.asyncio
async def test_api_health(client):
    res = await client.get("/api/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "online"
    assert data["temperatura"] == 0.0
    assert data["modelo_objetivo"] == "gpt-4o"

@pytest.mark.asyncio
async def test_api_tecnicas(client):
    res = await client.get("/api/tecnicas")
    assert res.status_code == 200
    tecnicas = res.json()
    assert len(tecnicas) == 4
    codigos = [t["codigo"] for t in tecnicas]
    assert "ZERO_SHOT" in codigos
    assert "FEW_SHOT" in codigos
    assert "CHAIN_OF_THOUGHT" in codigos
    assert "ROLE_PROMPTING" in codigos

@pytest.mark.asyncio
async def test_api_problemas_list(client):
    res = await client.get("/api/problemas")
    assert res.status_code == 200
    problemas = res.json()
    assert len(problemas) >= 1
    p = problemas[0]
    assert "ejemplos_enunciado" in p
    assert "ejemplos_few_shot" in p
    assert "pruebas_funcionales" in p
    assert isinstance(p["ejemplos_enunciado"], list)
    assert isinstance(p["ejemplos_few_shot"], list)
    assert isinstance(p["pruebas_funcionales"], list)

@pytest.mark.asyncio
async def test_api_prompts_preview(client):
    probs_res = await client.get("/api/problemas")
    probs = probs_res.json()
    prob_id = probs[0]["problema_id"]

    res = await client.post("/api/prompts/preview", json={
        "problema_id": prob_id,
        "tecnica_codigo": "FEW_SHOT"
    })
    assert res.status_code == 200
    data = res.json()
    assert "prompt" in data
    assert len(data["prompt"]) > 50
    assert data["tecnica_codigo"] == "FEW_SHOT"

@pytest.mark.asyncio
async def test_api_execution_pipeline_and_duplicate_protection(client, monkeypatch):
    """
    Verifica el pipeline sin invocar el proveedor ni sobrescribir datos experimentales.
    """
    import uuid

    solution = "class Solution:\n    def addOne(self, value):\n        return value + 1\n"

    async def fake_generate_solution(prompt, problema, tecnica_codigo):
        return {
            "modo": "test",
            "modelo": "gpt-4o-test",
            "duracion_ms": 1.0,
            "respuesta_completa": solution,
            "motivo_finalizacion": "stop",
            "parametros": {"model": "gpt-4o-test", "temperature": 0.0},
            "uso_tokens": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }

    monkeypatch.setattr(
        "backend.routers.ejecuciones.openai_service.generate_solution",
        fake_generate_solution,
    )
    imported = await client.post("/api/problemas/importar-json", json={
        "codigo": f"TEST-EXEC-{uuid.uuid4().hex}",
        "titulo": "API execution test",
        "plataforma_origen": "LeetCode",
        "dificultad": "Fácil",
        "categoria_algoritmica": "Testing",
        "enunciado": "Return one more than the input.",
        "solucion_referencia": solution,
        "ejemplos_enunciado": [{"entrada": "1", "salida": "2"}],
        "ejemplos_few_shot": [],
        "pruebas_funcionales": [
            {"nombre": "add_one", "codigo": "assert Solution().addOne(1) == 2"}
        ],
    })
    assert imported.status_code == 200
    prob_id = imported.json()[0]["problema_id"]

    res1 = await client.post("/api/ejecutar", json={
        "problema_id": prob_id,
        "tecnica_codigo": "ZERO_SHOT",
        "numero_repeticion": 1
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["estado_ejecucion"] == "completada"
    assert data1["codigo_parseable"] is True
    assert data1["porcentaje_pruebas_aprobadas"] == 100.0
    assert data1["maintainability_index"] is not None
    assert data1["tiempo_promedio_ms"] is not None
    assert data1["memoria_mediana_kb"] is not None

    hash1 = data1["hash_codigo_sha256"]
    assert len(hash1) == 64

    res2 = await client.post("/api/ejecutar", json={
        "problema_id": prob_id,
        "tecnica_codigo": "ZERO_SHOT",
        "numero_repeticion": 2
    })
    assert res2.status_code == 200
    data2 = res2.json()
    hash2 = data2["hash_codigo_sha256"]

    assert hash1 == hash2

    duplicate = await client.post("/api/ejecutar", json={
        "problema_id": prob_id,
        "tecnica_codigo": "ZERO_SHOT",
        "numero_repeticion": 1
    })
    assert duplicate.status_code == 409
    await execute_dml(
        "DELETE FROM ejecucion_experimental WHERE problema_id = :id",
        {"id": prob_id},
    )
    await execute_dml("DELETE FROM problema WHERE problema_id = :id", {"id": prob_id})

@pytest.mark.asyncio
async def test_api_metricas_matriz(client):
    res = await client.get("/api/metricas/matriz")
    assert res.status_code == 200
    rows = res.json()
    assert isinstance(rows, list)
    if rows:
        row = rows[0]
        assert "porcentaje_pruebas_aprobadas" in row
        assert "maintainability_index" in row
        assert "tiempo_promedio_ms" in row
        assert "hash_codigo_sha256" in row

@pytest.mark.asyncio
async def test_api_metricas_resumen_tecnicas(client):
    res = await client.get("/api/metricas/resumen-tecnicas")
    assert res.status_code == 200
    summaries = res.json()
    assert len(summaries) == 4

@pytest.mark.asyncio
async def test_api_export_csv(client):
    res = await client.get("/api/export/csv")
    assert res.status_code == 200
    assert "text/csv" in res.headers["content-type"]
    assert "ejecucion_id" in res.text
    assert "version_plantilla_prompt" in res.text
    assert "hash_prompt" in res.text

@pytest.mark.asyncio
async def test_api_export_json(client):
    res = await client.get("/api/export/json")
    assert res.status_code == 200
    assert "application/json" in res.headers["content-type"]
    data = res.json()
    assert "metadata" in data
    assert "registros" in data
    if data["registros"]:
        assert "version_plantilla_prompt" in data["registros"][0]
        assert "hash_prompt" in data["registros"][0]

@pytest.mark.asyncio
async def test_api_importar_json(client):
    import uuid

    problem_code = f"LC-999-TEST-{uuid.uuid4().hex}"
    problem_payload = {
        "codigo": problem_code,
        "titulo": "Test Problem for JSON Import",
        "plataforma_origen": "LeetCode",
        "dificultad": "Fácil",
        "categoria_algoritmica": "Testing",
        "enunciado": "Enunciado de prueba para importación JSON",
        "ejemplos_enunciado": [{"entrada": "x=1", "salida": "1"}],
        "ejemplos_few_shot": [{"id": 1, "descripcion": "Demo test", "entrada": "x=2", "salida": "2"}],
        "pruebas_funcionales": [{"nombre": "test_import", "codigo": "assert True"}]
    }
    res = await client.post("/api/problemas/importar-json", json=problem_payload)
    assert res.status_code == 200
    results = res.json()
    assert len(results) == 1
    assert results[0]["codigo"] == problem_code
    assert results[0]["cantidad_ejemplos_few_shot"] == 1
    await execute_dml(
        "DELETE FROM problema WHERE codigo = :codigo",
        {"codigo": problem_code},
    )
