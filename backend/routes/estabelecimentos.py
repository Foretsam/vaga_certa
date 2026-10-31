from typing import List
from fastapi import APIRouter, HTTPException, status
from database import db
from schemas import AndarPayload, EstabelecimentoSavePayload

router = APIRouter()


async def gravar_andares_e_mapa(
    cursor, id_estabelecimento: int, andares: List[AndarPayload]
):
    for andar in andares:
        await cursor.execute(
            """
            INSERT INTO andares (id_estabelecimento, nome_andar, grid_x, grid_y)
            VALUES (%s, %s, %s, %s)
            """,
            (id_estabelecimento, andar.nome_andar.strip(), andar.grid_x, andar.grid_y),
        )
        id_andar_banco = cursor.lastrowid

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

        mapa_equipamentos_id = {}

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


@router.get("/estabelecimentos")
async def listar_estabelecimentos_completos():
    estabelecimentos_rows = await db.fetch("""
        SELECT e.id_estabelecimento AS id, e.nome, e.cidade, e.inativo,
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
                SELECT v.id_vaga, v.identificador, v.coord_x, v.coord_y,
                       v.livre_para_estacionar, v.inativo,
                       eq.id_equipamento, eq.codigo_mac,
                       s.id_setor, s.nome_setor, s.prefixo, s.cor_hex
                FROM vagas v
                JOIN equipamentos eq ON v.id_equipamento = eq.id_equipamento
                JOIN setores s ON eq.id_setor = s.id_setor
                WHERE s.id_andar = %s
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
                            "inativo": bool(v["inativo"]),
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
                "cidade": est.get("cidade") or "Sorocaba",
                "id_usuario": est["id_usuario"],
                "inativo": bool(est["inativo"]),
                "andares": andares_formatados,
            }
        )

    return resultado


@router.post("/estabelecimentos", status_code=status.HTTP_201_CREATED)
async def criar_estabelecimento(payload: EstabelecimentoSavePayload):
    cidade_limpa = (payload.cidade or "Sorocaba").strip()
    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await conn.begin()
                await cursor.execute(
                    "INSERT INTO estabelecimentos (nome, cidade) VALUES (%s, %s)",
                    (payload.nome.strip(), cidade_limpa),
                )
                id_est = cursor.lastrowid

                await cursor.execute(
                    "INSERT INTO usuario_estabelecimento (id_usuario, id_estabelecimento) VALUES (%s, %s)",
                    (payload.id_usuario, id_est),
                )

                # Se o usuário vinculado era 'usuario' (motorista), promove para 'admin_estabelecimento' (gerente)
                await cursor.execute(
                    """
                    UPDATE usuarios
                    SET nivel_acesso = 'admin_estabelecimento'
                    WHERE id_usuario = %s AND nivel_acesso = 'usuario'
                    """,
                    (payload.id_usuario,),
                )

                await gravar_andares_e_mapa(cursor, id_est, payload.andares)
                await conn.commit()
                return {"status": "sucesso", "id_estabelecimento": id_est}
            except Exception as e:
                await conn.rollback()
                raise HTTPException(
                    status_code=400, detail=f"Erro ao salvar no banco: {str(e)}"
                )


@router.put("/estabelecimentos/{id_estabelecimento}")
async def atualizar_estabelecimento(
    id_estabelecimento: int, payload: EstabelecimentoSavePayload
):
    cidade_limpa = (payload.cidade or "Sorocaba").strip()
    async with db.pool.acquire() as conn:
        async with conn.cursor() as cursor:
            try:
                await conn.begin()
                await cursor.execute(
                    "UPDATE estabelecimentos SET nome = %s, cidade = %s WHERE id_estabelecimento = %s",
                    (payload.nome.strip(), cidade_limpa, id_estabelecimento),
                )

                await cursor.execute(
                    "DELETE FROM usuario_estabelecimento WHERE id_estabelecimento = %s",
                    (id_estabelecimento,),
                )
                await cursor.execute(
                    "INSERT INTO usuario_estabelecimento (id_usuario, id_estabelecimento) VALUES (%s, %s)",
                    (payload.id_usuario, id_estabelecimento),
                )

                # Se o usuário vinculado era 'usuario' (motorista), promove para 'admin_estabelecimento' (gerente)
                await cursor.execute(
                    """
                    UPDATE usuarios
                    SET nivel_acesso = 'admin_estabelecimento'
                    WHERE id_usuario = %s AND nivel_acesso = 'usuario'
                    """,
                    (payload.id_usuario,),
                )

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


@router.patch("/estabelecimentos/{id_estabelecimento}/status")
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


@router.delete("/estabelecimentos/{id_estabelecimento}")
async def deletar_estabelecimento(id_estabelecimento: int):
    linhas = await db.execute(
        "DELETE FROM estabelecimentos WHERE id_estabelecimento = %s",
        (id_estabelecimento,),
    )
    if linhas == 0:
        raise HTTPException(status_code=404, detail="Estabelecimento não encontrado.")
    return {"status": "sucesso"}
