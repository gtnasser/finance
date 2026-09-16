import asyncio

from database import AsyncSessionLocal
from seed import seed_plano_contas

async def main() -> None:
    async with AsyncSessionLocal() as session:
        criados = await seed_plano_contas(session)
        print(f"Contas criadas no plano de contas: {criados}")

if __name__ == "__main__":
    asyncio.run(main())