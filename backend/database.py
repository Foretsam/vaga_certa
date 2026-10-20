import aiomysql


class Database:
    def __init__(self):
        self.pool: aiomysql.Pool | None = None

    async def connect(self):
        if self.pool is not None:
            return
        self.pool = await aiomysql.create_pool(
            minsize=1,
            maxsize=10,
            host="127.0.0.1",
            port=3306,
            user="root",
            password="",
            db="vagacerta_db",
            autocommit=True,
            cursorclass=aiomysql.DictCursor,
        )
        print("[DB] ✅ Conectado ao MySQL (vagacerta_db) com sucesso.")

    async def close(self):
        if self.pool is not None:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None

    async def execute(self, query: str, params: tuple = ()) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.lastrowid or cursor.rowcount

    async def fetch(self, query: str, params: tuple = (), one: bool = False):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                if one:
                    return await cursor.fetchone()
                return await cursor.fetchall()


db = Database()
