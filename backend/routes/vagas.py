from fastapi import APIRouter
from database import db
from schemas import LoteStatusVagasPayload

router = APIRouter()


@router.patch("/vagas/status-lote")
async def alterar_status_vagas_em_lote(payload: LoteStatusVagasPayload):
    if not payload.ids_vagas:
        return {"status": "sucesso", "afetadas": 0}

    placeholders = ",".join(["%s"] * len(payload.ids_vagas))
    novo_valor = 1 if payload.inativo else 0
    params = tuple([novo_valor, novo_valor] + payload.ids_vagas)

    await db.execute(
        f"""
        UPDATE vagas
        SET inativo = %s,
            data_inativacao = IF(%s = 1, CURRENT_TIMESTAMP(), NULL)
        WHERE id_vaga IN ({placeholders})
        """,
        params,
    )
    return {"status": "sucesso", "inativo": payload.inativo}
