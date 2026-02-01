import asyncpg
from typing import AsyncGenerator
from contextlib import asynccontextmanager

@asynccontextmanager
async def get_pg_connection() -> AsyncGenerator[None, asyncpg.Connection]:
    # TODO: 1. При каждом обращении к БД создается новое соединение
    # TODO: 2. Не учитывается работа в транзакции

    connection: asyncpg.Connection = await asyncpg.connect(
        user='postgres',
        password='postgres',
        database='avito',
        host='localhost',
        port=5432
    )

    yield connection

    await connection.close()