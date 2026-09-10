from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr

# -----

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    email: Optional[str] = None

# -----

class UsuarioCreate(BaseModel):
    nome: str
    email: EmailStr
    senha: str

class UsuarioResponse(BaseModel):
    id: int
    nome: str
    email: EmailStr
    ativo: bool
    created_at: datetime

    class Config:
        from_attributes = True

# -----

