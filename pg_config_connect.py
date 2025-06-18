# ✅ 파일명: pg_config_connect.py

import os
import asyncio
from dotenv import load_dotenv
import asyncpg
import psycopg2  # 기존 동기식 연결을 위해 유지

# ✅ .env 파일 로드
load_dotenv()

# ✅ PostgreSQL 연결 함수 (동기식)
def get_pg_connection():
    PG_HOST = os.getenv("PG_HOST")
    PG_PORT = os.getenv("PG_PORT")
    PG_DATABASE = os.getenv("PG_DATABASE")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")

    return psycopg2.connect(
        host=PG_HOST,
        port=PG_PORT,
        dbname=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD
    )

# ✅ PostgreSQL 비동기 연결 함수
async def get_pg_pool():
    PG_HOST = os.getenv("PG_HOST")
    PG_PORT = os.getenv("PG_PORT")
    PG_DATABASE = os.getenv("PG_DATABASE")
    PG_USER = os.getenv("PG_USER")
    PG_PASSWORD = os.getenv("PG_PASSWORD")

    # 연결 풀 생성
    pool = await asyncpg.create_pool(
        host=PG_HOST,
        port=PG_PORT,
        database=PG_DATABASE,
        user=PG_USER,
        password=PG_PASSWORD,
        min_size=1,
        max_size=10
    )
    
    return pool
    
