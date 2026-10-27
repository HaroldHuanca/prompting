"""
Capa de conexión y persistencia a PostgreSQL con SQLAlchemy Async y asyncpg.
Utiliza NullPool para evitar conflictos de conexiones ligadas a bucles de eventos distintos en asyncpg.
"""
from typing import AsyncGenerator, Any, List, Dict
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool
from sqlalchemy import text
from backend.config import DATABASE_URL

engine = create_async_engine(
    DATABASE_URL,
    echo=False,
    future=True,
    poolclass=NullPool,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Generador de sesiones asíncronas para inyección de dependencias en FastAPI."""
    async with AsyncSessionLocal() as session:
        try:
            await session.execute(text("SET search_path TO experimento, public;"))
            yield session
        finally:
            await session.close()

async def fetch_all(query: str, params: Dict[str, Any] = None) -> List[Dict[str, Any]]:
    """Ejecuta una consulta SQL y retorna una lista de diccionarios con los resultados."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET search_path TO experimento, public;"))
        result = await session.execute(text(query), params or {})
        columns = result.keys()
        rows = result.fetchall()
        # Si la consulta contiene DML (INSERT/UPDATE/DELETE RETURNING), hacer commit
        query_upper = query.strip().upper()
        if any(query_upper.startswith(cmd) for cmd in ("INSERT", "UPDATE", "DELETE")):
            await session.commit()
        return [dict(zip(columns, row)) for row in rows]

async def fetch_one(query: str, params: Dict[str, Any] = None) -> Dict[str, Any] | None:
    """Ejecuta una consulta SQL y retorna la primera fila como diccionario o None."""
    rows = await fetch_all(query, params)
    return rows[0] if rows else None

async def execute_dml(query: str, params: Dict[str, Any] = None) -> None:
    """Ejecuta una sentencia de inserción, actualización o eliminación con commit explícito."""
    async with AsyncSessionLocal() as session:
        await session.execute(text("SET search_path TO experimento, public;"))
        await session.execute(text(query), params or {})
        await session.commit()
