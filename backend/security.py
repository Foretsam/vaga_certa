import hashlib
import hmac
import re
import secrets
from fastapi import HTTPException


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
