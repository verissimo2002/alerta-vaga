"""
Pydantic Schemas - Validação e serialização de dados
"""

from pydantic import BaseModel, EmailStr
from datetime import datetime
from typing import Optional


class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    telefone: str
    servico: str
    numero_passaporte: Optional[str] = None
    codigo_consulado: Optional[str] = None
    status: Optional[str] = "pendente"


class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[EmailStr] = None
    telefone: Optional[str] = None
    servico: Optional[str] = None
    numero_passaporte: Optional[str] = None
    codigo_consulado: Optional[str] = None
    status: Optional[str] = None
    agendada: Optional[bool] = None
    hora_agendada: Optional[str] = None


class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: str
    telefone: str
    servico: str
    numero_passaporte: Optional[str]
    codigo_consulado: Optional[str]
    data_agendada: Optional[datetime]
    hora_agendada: Optional[str]
    agendada: bool
    status: Optional[str]
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


class HistoricoAlertaResponse(BaseModel):
    id: int
    usuario_id: int
    servico: str
    data_disponivel: datetime
    notificado: bool
    criado_em: datetime

    class Config:
        from_attributes = True


class HistoricoAgendamentoResponse(BaseModel):
    id: int
    usuario_id: int
    servico: str
    data_agendada: datetime
    status: str
    tentativas: int
    mensagem_erro: Optional[str]
    criado_em: datetime

    class Config:
        from_attributes = True
