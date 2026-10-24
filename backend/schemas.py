from typing import List, Optional
from pydantic import BaseModel


class SetorPayload(BaseModel):
    id_temp: int
    nome_setor: str
    prefixo: str
    cor_hex: str


class CelulaPreenchidaPayload(BaseModel):
    x: int
    y: int
    tipo: str
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


class CadastroUsuarioPayload(BaseModel):
    nome: str
    email: str
    senha: str


class LoginUsuarioPayload(BaseModel):
    email: str
    senha: str


class LoteStatusVagasPayload(BaseModel):
    ids_vagas: List[int]
    inativo: bool
