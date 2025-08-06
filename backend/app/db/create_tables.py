import asyncio
from backend.app.db.database import engine, async_engine, Base, AsyncSessionLocal
from backend.app.models import notion_integration  # импорт модели


async def async_create_tables():
    print("Создаю таблицы...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Таблицы созданы")


def create_tables():
    print("Создаю таблицы...")
    # Base.metadata.drop_all(engine)
    Base.metadata.create_all(bind=engine)
    print("Таблицы созданы")


if __name__ == "__main__":
    asyncio.run(async_create_tables())
    create_tables()
