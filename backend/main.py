from contextlib import asynccontextmanager
from typing import List, Optional
import hashlib
import hmac
import re
import secrets
from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.close()


app = FastAPI(title="API Vaga Certa", lifespan=lifespan)

# Libera o CORS para que o Vue (Vite) consiga fazer requisições ao FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =========================================================
# MODELOS PYDANTIC (VALIDAÇÃO DO PAYLOAD DO EDITOR 2D)
# =========================================================
class SetorPayload(BaseModel):
    id_temp: int
    nome_setor: str
    prefixo: str
    cor_hex: str


class CelulaPreenchidaPayload(BaseModel):
    x: int
    y: int
    tipo: str  # 'ESTRADA' | 'ENTRADA' | 'SAIDA' | 'ACESSO' | 'FUNDO_SETOR' | 'VAGA'
    orientacao: str = "NENHUMA"
    setor_id_temp: Optional[int] = None
    identificador: Optional[str] = None
    livre: Optional[bool] = True
    mac_esp: Optional[str] = None


class AndarPayload(BaseModel):
    nome_andar: str
    grid_x: int
    grid_y: int
    setores: List[SetorPayload]
    celulas_preenchidas: List[CelulaPreenchidaPayload]


class EstabelecimentoSavePayload(BaseModel):
    nome: str
    id_usuario: int
    andares: List[AndarPayload]


# =========================================================
# FUNÇÃO AUXILIAR DE PERSISTÊNCIA DO MAPA 2D EM TRANSAÇÃO
# =========================================================
async def gravar_andares_e_mapa(
    cursor, id_estabelecimento: int, andares: List[AndarPayload]
):
    for andar in andares:
        # 1. Insere o Andar
        await cursor.execute(
            """
            INSERT INTO andares (id_estabelecimento, nome_andar, grid_x, grid_y)
            VALUES (%s, %s, %s, %s)
            """,
            (id_estabelecimento, andar.nome_andar.strip(), andar.grid_x, andar.grid_y),
        )
        id_andar_banco = cursor.lastrowid

        # 2. Insere os Setores do andar e guarda o mapa { id_temp_do_vue : id_setor_do_mysql }
        mapa_setores_id = {}
        for setor in andar.setores:
            await cursor.execute(
                """
                INSERT INTO setores (id_andar, nome_setor, prefixo, cor_hex)
                VALUES (%s, %s, %s, %s)
                """,
                (
                    id_andar_banco,
                    setor.nome_setor.strip(),
                    setor.prefixo.strip().upper(),
                    setor.cor_hex,
                ),
            )
            mapa_setores_id[setor.id_temp] = cursor.lastrowid

        # 3. Cache local para não recriar o mesmo equipamento (id_setor + codigo_mac) várias vezes
        mapa_equipamentos_id = {}

        # 4. Percorre apenas os quadrados não-vazios enviados pelo Editor 2D
        for cel in andar.celulas_preenchidas:
            id_setor_real = (
                mapa_setores_id.get(cel.setor_id_temp) if cel.setor_id_temp else None
            )

            if cel.tipo == "VAGA":
                if not id_setor_real or not cel.mac_esp:
                    raise HTTPException(
                        status_code=400,
                        detail=f"A vaga na coordenada ({cel.x},{cel.y}) está sem setor ou sem MAC de equipamento.",
                    )
                chave_eq = (id_setor_real, cel.mac_esp.strip().upper())
                if chave_eq not in mapa_equipamentos_id:
                    await cursor.execute(
                        """
                        INSERT INTO equipamentos (id_setor, codigo_mac)
                        VALUES (%s, %s)
                        """,
                        (id_setor_real, cel.mac_esp.strip().upper()),
                    )
                    mapa_equipamentos_id[chave_eq] = cursor.lastrowid

                id_equip_real = mapa_equipamentos_id[chave_eq]

                await cursor.execute(
                    """
                    INSERT INTO vagas (id_equipamento, identificador, coord_x, coord_y, livre_para_estacionar)
                    VALUES (%s, %s, %s, %s, %s)
                    """,
                    (
                        id_equip_real,
                        (cel.identificador or "V1").strip().upper(),
                        cel.x,
                        cel.y,
                        1 if cel.livre else 0,
                    ),
                )
            else:
                # Elementos estruturais: ESTRADA, ENTRADA, SAIDA, ACESSO ou FUNDO_SETOR
                orientacao = (
                    cel.orientacao
                    if cel.orientacao in ("H", "V", "NENHUMA")
                    else "NENHUMA"
                )
                await cursor.execute(
                    """
                    INSERT INTO elementos_mapa (id_andar, id_setor, tipo, orientacao, coord_x, coord_y)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (id_andar_banco, id_setor_real, cel.tipo, orientacao, cel.x, cel.y),
                )


# =========================================================
# ROTAS DA API
# =========================================================


@app.get("/usuarios")
async def listar_usuarios():
    usuarios = await db.fetch(
        "SELECT id_usuario, nome, email, nivel_acesso FROM usuarios WHERE inativo = 0 ORDER BY id_usuario"
    )
    return usuarios


@app.get("/estabelecimentos")
async def listar_estabelecimentos_completos():
    """Retorna todos os estabelecimentos com seus andares, setores, vagas e elementos do mapa."""
    estabelecimentos_rows = await db.fetch("""
        SELECT e.id_estabelecimento AS id, e.nome, e.inativo,
               COALESCE(ue.id_usuario, 1) AS id_usuario
        FROM estabelecimentos e
        LEFT JOIN usuario_estabelecimento ue ON e.id_estabelecimento = ue.id_estabelecimento
        ORDER BY e.id_estabelecimento ASC
        """)

    resultado = []
    for est in estabelecimentos_rows:
        id_est = est["id"]
        andares_rows = await db.fetch(
            """
            SELECT id_andar, nome_andar, grid_x, grid_y
            FROM andares
            WHERE id_estabelecimento = %s AND inativo = 0
            ORDER BY id_andar ASC
            """,
            (id_est,),
        )

        andares_formatados = []
        for andar in andares_rows:
            id_andar = andar["id_andar"]

            setores_rows = await db.fetch(
                """
                SELECT id_setor, nome_setor, prefixo, cor_hex, inativo AS inativo_offline
                FROM setores
                WHERE id_andar = %s
                ORDER BY id_setor ASC
                """,
                (id_andar,),
            )

            elementos_rows = await db.fetch(
                """
                SELECT id_elemento, id_setor, tipo, orientacao, coord_x, coord_y
                FROM elementos_mapa
                WHERE id_andar = %s
                """,
                (id_andar,),
            )

            vagas_rows = await db.fetch(
                """
                SELECT v.id_vaga, v.identificador, v.coord_x, v.coord_y, v.livre_para_estacionar,
                       eq.id_equipamento, eq.codigo_mac,
                       s.id_setor, s.nome_setor, s.prefixo, s.cor_hex
                FROM vagas v
                JOIN equipamentos eq ON v.id_equipamento = eq.id_equipamento
                JOIN setores s ON eq.id_setor = s.id_setor
                WHERE s.id_andar = %s AND v.inativo = 0
                """,
                (id_andar,),
            )

            andares_formatados.append(
                {
                    "id_andar": id_andar,
                    "nome_andar": andar["nome_andar"],
                    "grid_x": andar["grid_x"],
                    "grid_y": andar["grid_y"],
                    "setores": [
                        {
                            "id_setor": s["id_setor"],
                            "nome_setor": s["nome_setor"],
                            "prefixo": s["prefixo"],
                            "cor_hex": s["cor_hex"],
                            "inativo_offline": bool(s["inativo_offline"]),
                        }
                        for s in setores_rows
                    ],
                    "elementos_mapa": elementos_rows,
                    "vagas": [
                        {
                            "id_vaga": v["id_vaga"],
                            "identificador": v["identificador"],
                            "coord_x": v["coord_x"],
                            "coord_y": v["coord_y"],
                            "livre": bool(v["livre_para_estacionar"]),
                            "mac_esp": v["codigo_mac"],
                            "id_setor": v["id_setor"],
                            "nome_setor": v["nome_setor"],
                            "prefixo": v["prefixo"],
                            "cor_hex": v["cor_hex"],
                        }
                        for v in vagas_rows
                    ],
                }
            )

        resultado.append(
            {
                "id": id_est,
                "nome": est["nome"],
                "id_usuario": est["id_usuario"],
                "inativo": bool(est["inativo"]),
                "andares": andares_formatados,
            }
        )

    return resultado


@app.post("/estabelecimentos", status_code=status.HTTP_201_CREATED)
async def criar_estabelecimento(payload: EstabelecimentoSavePayload):
    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await conn.begin()

                await cursor.execute(
                    "INSERT INTO estabelecimentos (nome) VALUES (%s)",
                    (payload.nome.strip(),),
                )
                id_est = cursor.lastrowid

                await cursor.execute(
                    "INSERT INTO usuario_estabelecimento (id_usuario, id_estabelecimento) VALUES (%s, %s)",
                    (payload.id_usuario, id_est),
                )

                await gravar_andares_e_mapa(cursor, id_est, payload.andares)

                await conn.commit()
                return {"status": "sucesso", "id_estabelecimento": id_est}
            except Exception as e:
                await conn.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Erro ao salvar no banco: {str(e)}"
                )


@app.put("/estabelecimentos/{id_estabelecimento}")
async def atualizar_estabelecimento(
    id_estabelecimento: int, payload: EstabelecimentoSavePayload
):
    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await conn.begin()

                await cursor.execute(
                    "UPDATE estabelecimentos SET nome = %s WHERE id_estabelecimento = %s",
                    (payload.nome.strip(), id_estabelecimento),
                )

                await cursor.execute(
                    "DELETE FROM usuario_estabelecimento WHERE id_estabelecimento = %s",
                    (id_estabelecimento,),
                )
                await cursor.execute(
                    "INSERT INTO usuario_estabelecimento (id_usuario, id_estabelecimento) VALUES (%s, %s)",
                    (payload.id_usuario, id_estabelecimento),
                )

                # Remove a estrutura anterior de andares (ON DELETE CASCADE limpa setores, vagas e elementos_mapa)
                # e grava a nova planta desenhada no Editor 2D
                await cursor.execute(
                    "DELETE FROM andares WHERE id_estabelecimento = %s",
                    (id_estabelecimento,),
                )

                await gravar_andares_e_mapa(cursor, id_estabelecimento, payload.andares)

                await conn.commit()
                return {"status": "sucesso", "id_estabelecimento": id_estabelecimento}
            except Exception as e:
                await conn.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Erro ao atualizar no banco: {str(e)}"
                )


@app.patch("/estabelecimentos/{id_estabelecimento}/status")
async def alternar_inativo_estabelecimento(id_estabelecimento: int):
    est = await db.fetch(
        "SELECT inativo FROM estabelecimentos WHERE id_estabelecimento = %s",
        (id_estabelecimento,),
        one=True,
    )
    if not est:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")

    novo_status = 0 if est["inativo"] else 1
    await db.execute(
        """
        UPDATE estabelecimentos
        SET inativo = %s,
            data_inativacao = IF(%s = 1, CURRENT_TIMESTAMP(), NULL)
        WHERE id_estabelecimento = %s
        """,
        (novo_status, novo_status, id_estabelecimento),
    )
    return {"status": "sucesso", "inativo": bool(novo_status)}


@app.delete("/estabelecimentos/{id_estabelecimento}")
async def deletar_estabelecimento(id_estabelecimento: int):
    linhas = await db.execute(
        "DELETE FROM estabelecimentos WHERE id_estabelecimento = %s",
        (id_estabelecimento,),
    )
    if linhas == 0:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")
    return {"status": "sucesso"}


class CadastroUsuarioPayload(BaseModel):
    nome: str
    email: str
    senha: str


class LoginUsuarioPayload(BaseModel):
    email: str
    senha: str


def gerar_hash_senha(senha: str) -> str:
    salt = secrets.token_hex(16)
    derivado = hashlib.pbkdf2_hmac(
        "sha256", senha.encode("utf-8"), salt.encode("utf-8"), 100_000
    ).hex()
    return f"pbkdf2_sha256${salt}${derivado}"


def verificar_hash_senha(senha_digitada: str, hash_salvo: str) -> bool:
    if not hash_salvo or "$" not in hash_salvo:
        return False
    try:
        algoritmo, salt, derivado_salvo = hash_salvo.split("$", 2)
        if algoritmo != "pbkdf2_sha256":
            return False
        derivado_teste = hashlib.pbkdf2_hmac(
            "sha256", senha_digitada.encode("utf-8"), salt.encode("utf-8"), 100_000
        ).hex()
        return hmac.compare_digest(derivado_teste, derivado_salvo)
    except Exception:
        return False


def validar_regras_senha(senha: str, email: str):
    if len(senha) < 8:
        raise HTTPException(
            status_code=400, detail="A senha deve ter ao menos 8 caracteres."
        )
    if " " in senha:
        raise HTTPException(
            status_code=400, detail="A senha não pode conter espaços em branco."
        )
    if not re.search(r"[A-Z]", senha):
        raise HTTPException(
            status_code=400, detail="A senha deve conter ao menos uma letra maiúscula."
        )
    if not re.search(r"[a-z]", senha):
        raise HTTPException(
            status_code=400, detail="A senha deve conter ao menos uma letra minúscula."
        )
    if not re.search(r"\d", senha):
        raise HTTPException(
            status_code=400, detail="A senha deve conter ao menos um número."
        )
    if not re.search(r"[^A-Za-z0-9]", senha):
        raise HTTPException(
            status_code=400, detail="A senha deve conter ao menos um símbolo."
        )

    email_limpo = email.strip().lower()
    usuario_email = email_limpo.split("@")[0] if "@" in email_limpo else email_limpo
    senha_lower = senha.lower()

    if senha_lower == email_limpo or (
        len(usuario_email) >= 3 and usuario_email in senha_lower
    ):
        raise HTTPException(
            status_code=400,
            detail="A senha não pode conter nem ser parecida com o seu endereço de e-mail.",
        )


@app.post("/auth/cadastro", status_code=status.HTTP_201_CREATED)
async def cadastrar_usuario(payload: CadastroUsuarioPayload):
    nome = payload.nome.strip()
    email = payload.email.strip().lower()
    senha = payload.senha

    if len(nome) < 3:
        raise HTTPException(
            status_code=400, detail="Informe seu nome completo (mínimo 3 caracteres)."
        )
    if not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
        raise HTTPException(
            status_code=400, detail="Informe um endereço de e-mail válido."
        )

    validar_regras_senha(senha, email)

    existente = await db.fetch(
        "SELECT id_usuario FROM usuarios WHERE email = %s",
        (email,),
        one=True,
    )
    if existente:
        raise HTTPException(
            status_code=409, detail="Este e-mail já está cadastrado no sistema."
        )

    senha_hash = gerar_hash_senha(senha)
    novo_id = await db.execute(
        """
        INSERT INTO usuarios (nome, email, senha_hash, nivel_acesso)
        VALUES (%s, %s, %s, 'usuario')
        """,
        (nome, email, senha_hash),
    )

    return {
        "status": "sucesso",
        "usuario": {
            "id_usuario": novo_id,
            "nome": nome,
            "email": email,
            "nivel_acesso": "usuario",
        },
    }


@app.post("/auth/login")
async def login_usuario(payload: LoginUsuarioPayload):
    email = payload.email.strip().lower()
    usuario = await db.fetch(
        """
        SELECT id_usuario, nome, email, senha_hash, nivel_acesso, inativo
        FROM usuarios
        WHERE email = %s
        """,
        (email,),
        one=True,
    )

    if not usuario or not verificar_hash_senha(payload.senha, usuario["senha_hash"]):
        raise HTTPException(status_code=401, detail="E-mail ou senha incorretos.")

    if usuario["inativo"]:
        raise HTTPException(
            status_code=403, detail="Esta conta está inativa. Contate o suporte."
        )

    return {
        "status": "sucesso",
        "usuario": {
            "id_usuario": usuario["id_usuario"],
            "nome": usuario["nome"],
            "email": usuario["email"],
            "nivel_acesso": usuario["nivel_acesso"],
        },
    }
