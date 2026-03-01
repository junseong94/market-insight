import psycopg2
from market_insight.utils.db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# posts 테이블
cur.execute("""
    CREATE TABLE IF NOT EXISTS posts (
        post_id      BIGINT PRIMARY KEY,
        stock_code   VARCHAR(20) NOT NULL,
        title        TEXT NOT NULL,
        content      TEXT,
        author       VARCHAR(100),
        views        INTEGER DEFAULT 0,
        likes        INTEGER DEFAULT 0,
        dislikes     INTEGER DEFAULT 0,
        created_at   VARCHAR(30),
        collected_at TIMESTAMP DEFAULT NOW()
    );
""")

# comments 테이블
cur.execute("""
    CREATE TABLE IF NOT EXISTS comments (
        comment_id   BIGINT PRIMARY KEY,
        post_id      BIGINT REFERENCES posts(post_id),
        author       VARCHAR(100),
        content      TEXT,
        likes        INTEGER DEFAULT 0,
        dislikes     INTEGER DEFAULT 0,
        created_at   VARCHAR(50),
        collected_at TIMESTAMP DEFAULT NOW()
    );
""")

conn.commit()
cur.close()
conn.close()

print("테이블 생성 완료: posts, comments")