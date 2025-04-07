import asyncpg
from dotenv import load_dotenv
import os
import logging

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

logger = logging.getLogger(__name__)

async def init_db():
    try:
        conn = await asyncpg.connect(DATABASE_URL)

        # Ensure uuid extension is enabled
        await conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')

        await conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email TEXT UNIQUE NOT NULL,
            password TEXT,
            role TEXT DEFAULT 'user',
            auth_provider TEXT DEFAULT 'email',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            session_name TEXT NOT NULL,
            response_format TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS messages (
            id SERIAL PRIMARY KEY,
            session_id UUID REFERENCES sessions(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            image_url TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS doctor_searches (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            query TEXT NOT NULL,
            specialty TEXT NOT NULL,
            location TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS feedback (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            message TEXT NOT NULL,
            specialty TEXT NOT NULL,
            feedback TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS medicines (
            id SERIAL PRIMARY KEY,
            name TEXT NOT NULL,
            country TEXT NOT NULL,
            condition TEXT NOT NULL,
            usage TEXT,
            overdose_effects TEXT,
            is_otc BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS otc_sources (
            id SERIAL PRIMARY KEY,
            country TEXT NOT NULL,
            url TEXT NOT NULL,
            selector TEXT NOT NULL,
            name_field TEXT NOT NULL,
            condition_field TEXT NOT NULL,
            active BOOLEAN DEFAULT TRUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE (country, url)
        );

        CREATE TABLE IF NOT EXISTS reminders (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            medicine TEXT NOT NULL,
            reminder_time TIME NOT NULL,
            frequency TEXT DEFAULT 'daily',
            status TEXT DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS refresh_tokens (
            id SERIAL PRIMARY KEY,
            user_id UUID REFERENCES users(id) ON DELETE CASCADE,
            token TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP NOT NULL,
            revoked BOOLEAN DEFAULT FALSE
        );

        CREATE TABLE IF NOT EXISTS reminder_history (
            id SERIAL PRIMARY KEY,
            user_id UUID NOT NULL,
            reminder_id INT NOT NULL REFERENCES reminders(id) ON DELETE CASCADE,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            delivery_status TEXT DEFAULT 'pending'
        );
        ''')
        logger.info("✅ Database tables initialized successfully")
        await conn.close()
    except Exception as e:
        logger.error(f"❌ Database initialization error: {str(e)}")
        raise

# ✅ Required by dependencies
async def get_db_connection():
    return await asyncpg.connect(DATABASE_URL)
