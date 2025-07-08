from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy import URL, create_engine, text


DATABASE_URL = "postgresql://myroslav:myroslav0818@localhost:5432/scheduloo"

sync_engine = create_engine(
    DATABASE_URL,
    echo=True
)

with sync_engine.connect() as conn:
    res = conn.execute(text('SELECT 1, 2, 3'))
    print(res.all())
