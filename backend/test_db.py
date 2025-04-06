import asyncio
from database import init_db, get_db_connection

async def test():
    await init_db()
    conn = await get_db_connection()
    tables = await conn.fetch("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    print("Tables in public schema:", [t["table_name"] for t in tables])
    await conn.close()

asyncio.run(test())