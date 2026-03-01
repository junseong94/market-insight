import psycopg2
from market_insight.utils.db_config import DB_CONFIG

conn = psycopg2.connect(**DB_CONFIG)
cur = conn.cursor()

# stocks 테이블 (종목 마스터)
cur.execute("""
    CREATE TABLE IF NOT EXISTS stocks (
        stock_code  VARCHAR(20) PRIMARY KEY,
        name        VARCHAR(100) NOT NULL,
        market      VARCHAR(10) NOT NULL,
        market_cap  BIGINT DEFAULT 0,
        rank        INTEGER,
        is_active   BOOLEAN DEFAULT TRUE,
        updated_at  TIMESTAMP DEFAULT NOW()
    );
""")

# themes 테이블 (테마 목록)
cur.execute("""
    CREATE TABLE IF NOT EXISTS themes (
        theme_code  VARCHAR(20) PRIMARY KEY,
        theme_name  VARCHAR(100) NOT NULL,
        updated_at  TIMESTAMP DEFAULT NOW()
    );
""")

# stock_themes 테이블 (종목-테마 N:N 매핑)
cur.execute("""
    CREATE TABLE IF NOT EXISTS stock_themes (
        stock_code  VARCHAR(20) REFERENCES stocks(stock_code),
        theme_code  VARCHAR(20) REFERENCES themes(theme_code),
        PRIMARY KEY (stock_code, theme_code)
    );
""")

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

print("테이블 생성 완료: stocks, themes, stock_themes, posts, comments")