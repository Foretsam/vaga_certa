from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from database import db
from routes import auth, estabelecimentos, vagas


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    try:
        await db.execute(
            """
            ALTER TABLE usuarios
            MODIFY nivel_acesso ENUM('admin_dev','admin_estabelecimento','usuario')
            NOT NULL DEFAULT 'usuario'
            """
        )
    except Exception:
        pass
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
