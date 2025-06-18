# create_tables.py

import asyncio
from pg_config_connect import get_pg_connection, get_pg_pool

# 기존 동기식 테이블 생성 함수
def create_tables():
    conn = get_pg_connection()
    cur = conn.cursor()

    # 스키마가 없으면 생성
    cur.execute("""
    CREATE SCHEMA IF NOT EXISTS notice_bot;
    """)

    # work_recommend 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notice_bot.work_recommend (
        record_key TEXT PRIMARY KEY,
        time TIMESTAMP,
        title TEXT,
        url TEXT,
        company TEXT,
        deadline TEXT,
        work_type TEXT
    );
    """)

    # work_general 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notice_bot.work_general (
        record_key TEXT PRIMARY KEY,
        time TIMESTAMP,
        title TEXT,
        url TEXT,
        company TEXT,
        deadline TEXT,
        work_type TEXT
    );
    """)

    # work_keywords 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS notice_bot.work_keywords (
        keyword TEXT PRIMARY KEY
    );
    """)

    # 기존 테이블에 work_type 열이 없으면 추가
    try:
        # work_recommend 테이블에 work_type 열 추가
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'notice_bot' AND table_name = 'work_recommend' AND column_name = 'work_type'
            ) THEN
                ALTER TABLE notice_bot.work_recommend ADD COLUMN work_type TEXT;
            END IF;
        END $$;
        """)

        # work_general 테이블에 work_type 열 추가
        cur.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM information_schema.columns 
                WHERE table_schema = 'notice_bot' AND table_name = 'work_general' AND column_name = 'work_type'
            ) THEN
                ALTER TABLE notice_bot.work_general ADD COLUMN work_type TEXT;
            END IF;
        END $$;
        """)
    except Exception as e:
        print(f"테이블 열 추가 중 오류 발생: {e}")

    # 키워드 데이터 초기화 및 삽입
    keyword_list = [
        '개발', '소프트웨어', 'AI', 'SW', 'QA',
        'FRONT', 'BACKEND', '프론트', '백엔드', 'FULLSTACK', '풀스택'
    ]

    cur.execute("DELETE FROM notice_bot.work_keywords;")
    cur.executemany(
        "INSERT INTO notice_bot.work_keywords (keyword) VALUES (%s) ON CONFLICT DO NOTHING;",
        [(kw,) for kw in keyword_list]
    )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ 테이블 생성 및 키워드 삽입 완료")

# 비동기식 테이블 생성 함수
async def create_tables_async():
    pool = await get_pg_pool()
    try:
        # 스키마가 없으면 생성
        await pool.execute("""
        CREATE SCHEMA IF NOT EXISTS notice_bot;
        """)

        # work_recommend 테이블
        await pool.execute("""
        CREATE TABLE IF NOT EXISTS notice_bot.work_recommend (
            record_key TEXT PRIMARY KEY,
            time TIMESTAMP,
            title TEXT,
            url TEXT,
            company TEXT,
            deadline TEXT,
            work_type TEXT
        );
        """)

        # work_general 테이블
        await pool.execute("""
        CREATE TABLE IF NOT EXISTS notice_bot.work_general (
            record_key TEXT PRIMARY KEY,
            time TIMESTAMP,
            title TEXT,
            url TEXT,
            company TEXT,
            deadline TEXT,
            work_type TEXT
        );
        """)

        # work_keywords 테이블
        await pool.execute("""
        CREATE TABLE IF NOT EXISTS notice_bot.work_keywords (
            keyword TEXT PRIMARY KEY
        );
        """)

        # 기존 테이블에 work_type 열이 없으면 추가
        try:
            # work_recommend 테이블에 work_type 열 추가
            await pool.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'notice_bot' AND table_name = 'work_recommend' AND column_name = 'work_type'
                ) THEN
                    ALTER TABLE notice_bot.work_recommend ADD COLUMN work_type TEXT;
                END IF;
            END $$;
            """)

            # work_general 테이블에 work_type 열 추가
            await pool.execute("""
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM information_schema.columns 
                    WHERE table_schema = 'notice_bot' AND table_name = 'work_general' AND column_name = 'work_type'
                ) THEN
                    ALTER TABLE notice_bot.work_general ADD COLUMN work_type TEXT;
                END IF;
            END $$;
            """)
        except Exception as e:
            print(f"테이블 열 추가 중 오류 발생: {e}")

        # 키워드 데이터 초기화 및 삽입
        keyword_list = [
            '개발', '소프트웨어', 'AI', 'SW', 'QA',
            'FRONT', 'BACKEND', '프론트', '백엔드', 'FULLSTACK', '풀스택'
        ]

        await pool.execute("DELETE FROM notice_bot.work_keywords;")
        
        # 키워드 삽입을 위한 트랜잭션
        async with pool.acquire() as conn:
            for keyword in keyword_list:
                await conn.execute(
                    "INSERT INTO notice_bot.work_keywords (keyword) VALUES ($1) ON CONFLICT DO NOTHING;",
                    keyword
                )
        
        print("✅ 테이블 생성 및 키워드 삽입 완료 (비동기)")
    finally:
        await pool.close()

# 비동기 실행을 위한 메인 함수
async def main_async():
    await create_tables_async()

if __name__ == "__main__":
    # 동기식 또는 비동기식 중 선택하여 실행
    # create_tables()  # 동기식 실행
    asyncio.run(main_async())  # 비동기식 실행
