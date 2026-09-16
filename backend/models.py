from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric,
    String, UniqueConstraint, func, text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base


# ---------- Mixins ----------

class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

class SoftDeleteMixin:
    """Exclusão lógica: registros nunca são apagados fisicamente."""
    deleted_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime, nullable=True, default=None, index=True
    )

# ---------- Autenticação ----------

class Usuario(TimestampMixin, Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(100), unique=True, index=True, nullable=False)
    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"), nullable=False)

# ---------- Plano de Contas ----------

class PlanoContas(TimestampMixin, SoftDeleteMixin, Base):
    """
    Plano de contas hierárquico.
    - `sintetica=True`  -> conta agrupadora (não recebe lançamento)
    - `sintetica=False` -> conta analítica (recebe lançamento)
    """

    __tablename__ = "plano_contas"
    __table_args__ = (
        UniqueConstraint("codigo", name="uq_plano_contas_codigo"),
        CheckConstraint(
            "tipo IN ('ATIVO','PASSIVO','PATRIMONIO_LIQUIDO','RECEITA','DESPESA')",
            name="ck_plano_contas_tipo",
        ),
        CheckConstraint(
            "natureza IN ('DEVEDORA','CREDORA')",
            name="ck_plano_contas_natureza",
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    codigo: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    descricao: Mapped[str] = mapped_column(String(150), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)
    natureza: Mapped[str] = mapped_column(String(10), nullable=False)
    sintetica: Mapped[bool] = mapped_column(Boolean, default=False, server_default=text("0"), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("plano_contas.id"), nullable=True, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"), nullable=False)

    parent: Mapped[Optional["PlanoContas"]] = relationship(
        remote_side="PlanoContas.id", back_populates="filhos"
    )
    filhos: Mapped[list["PlanoContas"]] = relationship(back_populates="parent")
    contas_correntes: Mapped[list["ContaCorrente"]] = relationship(
        back_populates="conta_plano"
    )

# ---------- Conta Corrente ----------

class ContaCorrente(TimestampMixin, SoftDeleteMixin, Base):
    __tablename__ = "contas_correntes"
    __table_args__ = (
        UniqueConstraint(
            "banco", "agencia", "numero", name="uq_conta_banco_agencia_numero"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False)
    banco: Mapped[str] = mapped_column(String(50), nullable=False)
    agencia: Mapped[str] = mapped_column(String(20), nullable=False)
    numero: Mapped[str] = mapped_column(String(30), nullable=False)
    tipo: Mapped[str] = mapped_column(String(30), nullable=False)  # Corrente, Poupança...
    moeda: Mapped[str] = mapped_column(String(3), default="BRL", server_default="BRL", nullable=False)
    saldo_inicial: Mapped[Decimal] = mapped_column(Numeric(14, 2), default=Decimal("0.00"), nullable=False)
    data_saldo_inicial: Mapped[date] = mapped_column(Date, nullable=False)
    plano_conta_id: Mapped[int] = mapped_column(ForeignKey("plano_contas.id"), nullable=False, index=True)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("1"), nullable=False)

    conta_plano: Mapped["PlanoContas"] = relationship(
        back_populates="contas_correntes"
    )