# repositories/base.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Generic, Optional, Sequence, TypeVar

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from database import Base

ModelT = TypeVar("ModelT", bound=Base)

def utcnow() -> datetime:
    """UTC ingênuo, compatível com colunas DateTime sem timezone."""
    return datetime.now(timezone.utc).replace(tzinfo=None)

class BaseRepository(Generic[ModelT]):
    model: type[ModelT]

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    def _base_stmt(self):
        stmt = select(self.model)
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        return stmt

    async def get(self, entity_id: int) -> Optional[ModelT]:
        stmt = self._base_stmt().where(self.model.id == entity_id)
        return (await self.session.execute(stmt)).scalar_one_or_none()

    async def list(
        self,
        *,
        limit: int = 50,
        offset: int = 0,
        order_by=None,
        filters: Optional[list] = None,
    ) -> Sequence[ModelT]:
        stmt = self._base_stmt()
        for cond in filters or []:
            stmt = stmt.where(cond)
        order_expr = order_by if order_by is not None else (self.model.id,)
        if not isinstance(order_expr, (tuple, list)):
            order_expr = (order_expr,)
        stmt = stmt.order_by(*order_expr)
        stmt = stmt.limit(limit).offset(offset)
        return (await self.session.execute(stmt)).scalars().all()

    async def count(self, *, filters: Optional[list] = None) -> int:
        stmt = select(func.count(self.model.id))
        if hasattr(self.model, "deleted_at"):
            stmt = stmt.where(self.model.deleted_at.is_(None))
        for cond in filters or []:
            stmt = stmt.where(cond)
        return int((await self.session.execute(stmt)).scalar_one())

    async def add(self, instance: ModelT) -> ModelT:
        self.session.add(instance)
        await self.session.flush()
        return instance

    async def soft_delete(self, instance: ModelT) -> None:
        instance.deleted_at = utcnow()
        await self.session.flush()