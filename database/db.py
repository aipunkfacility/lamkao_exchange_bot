from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from database.models import Base

DATABASE_URL = "sqlite+aiosqlite:///lamkao.db"

engine = create_async_engine(DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db() -> None:
    """Инициализация БД: создание всех таблиц."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session() -> AsyncSession:
    """Получение сессии БД (генератор)."""
    async with async_session() as session:
        yield session
