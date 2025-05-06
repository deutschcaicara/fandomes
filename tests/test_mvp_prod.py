import pytest
import httpx
import os

BASE_URL = "https://api.famdomes.com.br"
API_KEY = os.getenv("API_KEY", "sua_api_key_aqui")  # Use variável real ou .env.test

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

@pytest.mark.asyncio
async def test_openapi_exposta():
    async with httpx.AsyncClient() as client:
        r = await client.get(f"{BASE_URL}/openapi.json")
        assert r.status_code == 200
        assert "paths" in r.json()

@pytest.mark.asyncio
async def test_agendamento_comando_ia():
    payload = {
        "telefone": "559999999999",
        "nome": "Paciente Teste",
        "comando": "quero agendar"
    }
    async with httpx.AsyncClient() as client:
        r = await client.post(f"{BASE_URL}/ia-comando", headers=HEADERS, json=payload)
        assert r.status_code == 200
        json = r.json()
        assert "checkout_url" in json or "status" in json

@pytest.mark.asyncio
async def test_agendamento_comando_ia():
    payload = {
        "telefone": "559999999999",
        "nome": "Paciente Teste",
        "comando": "quero agendar"
    }

    header_variacoes = [
        {"X-API-Key": API_KEY, "Content-Type": "application/json"},
        {"x-api-key": API_KEY, "Content-Type": "application/json"},
    ]

    sucesso = False

    for headers in header_variacoes:
        async with httpx.AsyncClient() as client:
            r = await client.post(f"{BASE_URL}/ia-comando", headers=headers, json=payload)
            print(f"🧪 Tentando com headers {headers} → status {r.status_code}")
            if r.status_code == 200:
                sucesso = True
                break

    assert sucesso, "❌ Nenhuma variação de header foi aceita pela API. Verifique sua API_KEY em produção."

