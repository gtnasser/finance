import asyncio

from sqlalchemy import func, select

from database import AsyncSessionLocal
from models import PlanoContas

async def main() -> None:
    async with AsyncSessionLocal() as session:
        total = await session.scalar(select(func.count(PlanoContas.id)))
        print(f"Total de contas no plano: {total}")

if __name__ == "__main__":
    asyncio.run(main())