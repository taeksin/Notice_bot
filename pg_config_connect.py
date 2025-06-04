# ✅ 파일명: pg_config_connect.py

import os
from dotenv import load_dotenv
import psycopg2

# ✅ .env 파일 로드
load_dotenv()

# ✅ PostgreSQL 연결 함수
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
    
