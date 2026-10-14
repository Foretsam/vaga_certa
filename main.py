from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from database import db
from contextlib import asynccontextmanager


# Define o ciclo de vida do servidor (conecta ao banco ao ligar)
@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.connect()
    yield
    await db.close()


app = FastAPI(title="API Vaga Certa", lifespan=lifespan)


# --- MODELOS PYDANTIC ---
# Define a estrutura exata do JSON que esperamos receber do ESP32
class AtualizarVagaSchema(BaseModel):
    mac_esp: str
    identificador_vaga: str
    livre: bool


# --- ROTAS (ENDPOINTS) ---


@app.get("/status_vagas")
async def get_status_vagas():
    """Rota consumida pelo Frontend HTML para desenhar o painel."""

    query = """
        SELECT v.identificador, v.livre_para_estacionar, s.nome_setor 
        FROM vagas v
        JOIN equipamentos e ON v.id_equipamento = e.id_equipamento
        JOIN setores s ON e.id_setor = s.id_setor
        WHERE v.inativo = FALSE AND s.inativo = FALSE
        ORDER BY s.nome_setor, v.identificador
    """

    try:
        vagas = await db.fetch(query)
        # O FastAPI converte automaticamente os dicionários do aiomysql para JSON
        return {"vagas": vagas}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro interno: {str(e)}")


@app.post("/atualizar_vaga", status_code=status.HTTP_200_OK)
async def post_atualizar_vaga(dados: AtualizarVagaSchema):
    """Rota IoT consumida pelo ESP32 via método POST."""

    # 1. Encontrar o ID da vaga baseado no MAC do ESP32
    query_busca = """
        SELECT v.id_vaga, v.livre_para_estacionar 
        FROM vagas v
        JOIN equipamentos e ON v.id_equipamento = e.id_equipamento
        WHERE e.codigo_mac = %s AND v.identificador = %s LIMIT 1
    """
    vaga_banco = await db.fetch(
        query_busca, (dados.mac_esp, dados.identificador_vaga), one=True
    )

    if not vaga_banco:
        raise HTTPException(
            status_code=404, detail="Vaga ou MAC do ESP32 não encontrados."
        )

    id_vaga = vaga_banco["id_vaga"]
    status_atual_banco = bool(vaga_banco["livre_para_estacionar"])
    novo_status = dados.livre

    # 2. Se o status for o mesmo, o sensor apenas piscou. Evitamos log duplicado.
    if status_atual_banco == novo_status:
        return {
            "status": "ignorado",
            "mensagem": "O status da vaga já era o mesmo enviado.",
        }

    # 3. Atualizar o status atual na tabela vagas
    await db.execute(
        "UPDATE vagas SET livre_para_estacionar = %s WHERE id_vaga = %s",
        (novo_status, id_vaga),
    )

    # 4. Lógica de inteligência do Histórico de BI (Inserir Entrada / Fechar Saída)
    if not novo_status:
        # Carro ENTROU (vaga agora está ocupada / false)
        await db.execute(
            "INSERT INTO historico_ocupacao (id_vaga) VALUES (%s)", (id_vaga,)
        )
    else:
        # Carro SAIU (vaga agora está livre / true)
        await db.execute(
            """
            UPDATE historico_ocupacao 
            SET data_saida = CURRENT_TIMESTAMP 
            WHERE id_vaga = %s AND data_saida IS NULL 
            ORDER BY data_entrada DESC LIMIT 1
            """,
            (id_vaga,),
        )

    return {"status": "sucesso", "vaga": dados.identificador_vaga, "livre": novo_status}
