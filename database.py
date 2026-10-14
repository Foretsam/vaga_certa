import aiomysql
import asyncio


class Database:
    def __init__(self):
        self.pool = None

    async def connect(self):
        """Inicializa o pool de conexão assíncrona com o MySQL"""
        if self.pool is not None:
            return

        try:
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
            print("✅ Conectado ao MySQL com sucesso.")
        except Exception as e:
            print(f"❌ Falha ao conectar no banco: {e}")

    async def execute(self, query: str, params: tuple = ()) -> int:
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                return cursor.rowcount

    async def fetch(self, query: str, params: tuple = (), one: bool = False):
        async with self.pool.acquire() as conn:
            async with conn.cursor() as cursor:
                await cursor.execute(query, params)
                if one:
                    return await cursor.fetchone()
                return await cursor.fetchall()

    async def close(self):
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()


# Instância global
db = Database()
