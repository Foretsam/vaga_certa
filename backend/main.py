from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from routes import auth, estabelecimentos, vagas


async def garantir_migracoes_schema() -> None:
    """Garante que colunas e tipos recentes existam em bancos criados com versões anteriores."""
    try:
        await db.execute("""
            ALTER TABLE usuarios
            MODIFY nivel_acesso ENUM('admin_dev','admin_estabelecimento','usuario')
            NOT NULL DEFAULT 'usuario'
            """)
    except Exception:
        pass

    try:
        col_cidade = await db.fetch(
            "SHOW COLUMNS FROM estabelecimentos LIKE 'cidade'",
            one=True,
        )
        if not col_cidade:
            await db.execute("""
                ALTER TABLE estabelecimentos
                ADD COLUMN cidade VARCHAR(60) NOT NULL DEFAULT 'Sorocaba' AFTER nome
                """)
    except Exception:
        pass

    try:
        col_tutoriais = await db.fetch(
            "SHOW COLUMNS FROM usuarios LIKE 'tutoriais_vistos'",
            one=True,
        )
        if not col_tutoriais:
            await db.execute("""
                ALTER TABLE usuarios
                ADD COLUMN tutoriais_vistos TEXT DEFAULT NULL AFTER nivel_acesso
                """)
    except Exception:
        pass


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação FastAPI (conexão e encerramento do banco)."""
    await db.connect()
    await garantir_migracoes_schema()
    yield
    await db.close()


app = FastAPI(title="API Vaga Certa", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, tags=["Autenticação e Usuários"])
app.include_router(estabelecimentos.router, tags=["Estabelecimentos e Mapas 2D"])
app.include_router(vagas.router, tags=["Operação de Vagas"])
