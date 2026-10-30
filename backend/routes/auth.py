import json
import re
from fastapi import APIRouter, HTTPException, status
from database import db
from schemas import CadastroUsuarioPayload, LoginUsuarioPayload, TutorialVistoPayload
from security import gerar_hash_senha, verificar_hash_senha, validar_regras_senha

router = APIRouter()


def extrair_lista_tutoriais(valor_banco) -> list:
    if not valor_banco:
        return []
    try:
        dados = json.loads(valor_banco)
        return dados if isinstance(dados, list) else []
    except Exception:
        return []


@router.get("/usuarios")
async def listar_usuarios():
    return await db.fetch(
        "SELECT id_usuario, nome, email, nivel_acesso FROM usuarios WHERE inativo = 0 ORDER BY id_usuario"
    )


@router.post("/auth/cadastro", status_code=status.HTTP_201_CREATED)
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
        INSERT INTO usuarios (nome, email, senha_hash, nivel_acesso, tutoriais_vistos)
        VALUES (%s, %s, %s, 'usuario', '[]')
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
            "tutoriais_vistos": [],
        },
    }


@router.post("/auth/login")
async def login_usuario(payload: LoginUsuarioPayload):
    email = payload.email.strip().lower()
    usuario = await db.fetch(
        """
        SELECT id_usuario, nome, email, senha_hash, nivel_acesso, tutoriais_vistos, inativo
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
            "tutoriais_vistos": extrair_lista_tutoriais(
                usuario.get("tutoriais_vistos")
            ),
        },
    }


@router.patch("/usuarios/{id_usuario}/tutorial")
async def registrar_tutorial_visto(id_usuario: int, payload: TutorialVistoPayload):
    usuario = await db.fetch(
        "SELECT tutoriais_vistos FROM usuarios WHERE id_usuario = %s",
        (id_usuario,),
        one=True,
    )
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    lista_atual = extrair_lista_tutoriais(usuario.get("tutoriais_vistos"))
    rota_limpa = payload.rota.strip()
    if rota_limpa and rota_limpa not in lista_atual:
        lista_atual.append(rota_limpa)
        await db.execute(
            "UPDATE usuarios SET tutoriais_vistos = %s WHERE id_usuario = %s",
            (json.dumps(lista_atual), id_usuario),
        )

    return {"status": "sucesso", "tutoriais_vistos": lista_atual}
