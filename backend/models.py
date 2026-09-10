from datetime import datetime
#todo: from decimal import Decimal
#todo: from typing import List, Optional
from sqlalchemy import (
    String, Numeric, Boolean, Date, DateTime, ForeignKey, CheckConstraint, func
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

# Usa a sintaxe `Mapped[...]` e `mapped_column()` do SQLAlchemy 2.0 com tipos estáticos rigorosos.


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())