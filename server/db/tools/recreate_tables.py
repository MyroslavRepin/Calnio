import asyncio
from server.db.database import async_engine, Base


async def async_drop_and_create_all_tables():
    print("ВНИМАНИЕ: Все таблицы будут удалены и созданы заново!")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        print("Все таблицы удалены.")
        await conn.run_sync(Base.metadata.create_all)
        print("Все таблицы созданы заново.")

if __name__ == "__main__":
    asyncio.run(async_drop_and_create_all_tables())

