from datetime import date, datetime
from decimal import Decimal
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

TipoConta = Literal["ATIVO", "PASSIVO", "PATRIMONIO_LIQUIDO", "RECEITA", "DESPESA"]
Natureza = Literal["DEVEDORA", "CREDORA"]

# ---------- Autenticação ----------

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UsuarioCreate(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    email: EmailStr
    senha: str = Field(min_length=8, max_length=72)

class UsuarioResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    nome: str
    email: EmailStr
    ativo: bool
    created_at: datetime


# ---------- Plano de Contas ----------

class PlanoContasBase(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    descricao: str = Field(min_length=1, max_length=150)
    tipo: TipoConta
    natureza: Natureza
    sintetica: bool = False
    parent_id: Optional[int] = None
    ativo: bool = True

class PlanoContasCreate(PlanoContasBase):
    pass

class PlanoContasUpdate(BaseModel):
    codigo: Optional[str] = Field(default=None, max_length=20)
    descricao: Optional[str] = Field(default=None, max_length=150)
    tipo: Optional[TipoConta] = None
    natureza: Optional[Natureza] = None
    sintetica: Optional[bool] = None
    parent_id: Optional[int] = None
    ativo: Optional[bool] = None

class PlanoContasRead(PlanoContasBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime

# ---------- Conta Corrente ----------

class ContaCorrenteBase(BaseModel):
    nome: str = Field(min_length=1, max_length=100)
    banco: str = Field(min_length=1, max_length=50)
    agencia: str = Field(min_length=1, max_length=20)
    numero: str = Field(min_length=1, max_length=30)
    tipo: str = Field(min_length=1, max_length=30)
    moeda: str = Field(default="BRL", min_length=3, max_length=3)
    saldo_inicial: Decimal = Decimal("0.00")
    data_saldo_inicial: date
    plano_conta_id: int
    ativo: bool = True

class ContaCorrenteCreate(ContaCorrenteBase):
    pass

class ContaCorrenteUpdate(BaseModel):
    nome: Optional[str] = Field(default=None, max_length=100)
    banco: Optional[str] = Field(default=None, max_length=50)
    agencia: Optional[str] = Field(default=None, max_length=20)
    numero: Optional[str] = Field(default=None, max_length=30)
    tipo: Optional[str] = Field(default=None, max_length=30)
    moeda: Optional[str] = Field(default=None, min_length=3, max_length=3)
    saldo_inicial: Optional[Decimal] = None
    data_saldo_inicial: Optional[date] = None
    plano_conta_id: Optional[int] = None
    ativo: Optional[bool] = None

class ContaCorrenteRead(ContaCorrenteBase):
    model_config = ConfigDict(from_attributes=True)
    id: int
    created_at: datetime
    updated_at: datetime



