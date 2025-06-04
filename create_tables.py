# create_tables.py

from pg_config_connect import get_pg_connection

def create_tables():
    conn = get_pg_connection()
    cur = conn.cursor()

    # work_recommend 테이블
    cur.execute("""
    CREATE TABLE IF NOT EXISTS work_recommend (
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
    CREATE TABLE IF NOT EXISTS work_general (
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
    CREATE TABLE IF NOT EXISTS work_keywords (
        keyword TEXT PRIMARY KEY
    );
    """)

    # 키워드 데이터 초기화 및 삽입
    keyword_list = [
        '개발', '소프트웨어', 'AI', 'SW', 'QA',
        'FRONT', 'BACKEND', '프론트', '백엔드', 'FULLSTACK', '풀스택'
    ]

    cur.execute("DELETE FROM work_keywords;")
    cur.executemany(
        "INSERT INTO work_keywords (keyword) VALUES (%s) ON CONFLICT DO NOTHING;",
        [(kw,) for kw in keyword_list]
    )

    conn.commit()
    cur.close()
    conn.close()
    print("✅ 테이블 생성 및 키워드 삽입 완료")

if __name__ == "__main__":
    create_tables()
