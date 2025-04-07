# backend/run_migration.py
import asyncio
import asyncpg
import os
from dotenv import load_dotenv

load_dotenv()

async def run_migration():
    conn = await asyncpg.connect(os.getenv("DATABASE_URL"))
    await conn.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS is_verified BOOLEAN DEFAULT FALSE;")
    await conn.close()
    print("✅ Migration completed!")

asyncio.run(run_migration())
