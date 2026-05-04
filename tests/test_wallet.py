import asyncio
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from main import app


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_create_and_get_wallet(client):
    resp = await client.post("/api/v1/wallets/")
    assert resp.status_code == 201
    wallet_id = resp.json()["wallet_id"]

    resp = await client.get(f"/api/v1/wallets/{wallet_id}")
    assert resp.status_code == 200
    assert resp.json()["balance"] == "0.00"


@pytest.mark.asyncio
async def test_deposit(client):
    resp = await client.post("/api/v1/wallets/")
    wallet_id = resp.json()["wallet_id"]

    resp = await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100.50}
    )
    assert resp.status_code == 200
    assert resp.json()["balance"] == "100.50"


@pytest.mark.asyncio
async def test_withdraw_sufficient(client):
    resp = await client.post("/api/v1/wallets/")
    wallet_id = resp.json()["wallet_id"]
    await client.post(f"/api/v1/wallets/{wallet_id}/operation", json={"operation_type": "DEPOSIT", "amount": 50})
    resp = await client.post(f"/api/v1/wallets/{wallet_id}/operation",
                             json={"operation_type": "WITHDRAW", "amount": 30})
    assert resp.status_code == 200
    assert resp.json()["balance"] == "20.00"


@pytest.mark.asyncio
async def test_withdraw_insufficient(client):
    resp = await client.post("/api/v1/wallets/")
    wallet_id = resp.json()["wallet_id"]
    resp = await client.post(f"/api/v1/wallets/{wallet_id}/operation",
                             json={"operation_type": "WITHDRAW", "amount": 10})
    assert resp.status_code == 400
    assert "Insufficient funds" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_wallet_not_found(client):
    resp = await client.get("/api/v1/wallets/00000000-0000-0000-0000-000000000000")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_concurrent_withdrawals(client):
    resp = await client.post("/api/v1/wallets/")
    wallet_id = resp.json()["wallet_id"]
    await client.post(
        f"/api/v1/wallets/{wallet_id}/operation",
        json={"operation_type": "DEPOSIT", "amount": 100}
    )

    async def try_withdraw(amount, attempt_id):
        resp = await client.post(
            f"/api/v1/wallets/{wallet_id}/operation",
            json={"operation_type": "WITHDRAW", "amount": amount}
        )
        return resp.status_code

    tasks = [try_withdraw(20, i) for i in range(10)]
    results = await asyncio.gather(*tasks)

    success_count = sum(1 for status in results if status == 200)
    failure_count = sum(1 for status in results if status == 400)

    assert success_count <= 5
    assert failure_count >= 5

    resp = await client.get(f"/api/v1/wallets/{wallet_id}")
    final_balance = float(resp.json()["balance"])
    assert final_balance == 0.0