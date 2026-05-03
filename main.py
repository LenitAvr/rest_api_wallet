from contextlib import asynccontextmanager
from fastapi import FastAPI
from db.session import engine, Base
from endpoints.wallet_endpoints import router as wallet_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Создаём таблицы при запуске
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Очистка при остановке
    await engine.dispose()


app = FastAPI(title="Wallet API", lifespan=lifespan)

app.include_router(wallet_router)

@app.get("/")
async def root():
    return {"message": "Wallet API is running"}