import asyncio
from twisterlab.database.session import AsyncSessionLocal
from twisterlab.database.models.trading import LiveOrderRecord
from sqlalchemy import update

async def reset():
    async with AsyncSessionLocal() as db:
        await db.execute(update(LiveOrderRecord).values(is_active=False))
        await db.commit()
        print('Cleaned up exposure')

if __name__ == "__main__":
    asyncio.run(reset())
