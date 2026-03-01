import psycopg2
from market_insight.utils.db_config import DB_CONFIG


class PostgresStorage:
    def __init__(self):
        self.conn = psycopg2.connect(**DB_CONFIG)

    # 게시글 + 댓글 한번에 저장
    # UPSERT: 같은 post_id가 있으면 UPDATE, 없으면 INSERT
    def save_posts(self, posts):
        cur = self.conn.cursor()

        for post in posts:
            if not post.get("post_id"):  # 클린봇 숨김 등 post_id 없으면 스킵
                continue

            # 게시글 UPSERT
            cur.execute("""
                INSERT INTO posts (post_id, stock_code, title, content, author, views, likes, dislikes, created_at)
                VALUES (%(post_id)s, %(stock_code)s, %(title)s, %(content)s, %(author)s, %(views)s, %(likes)s, %(dislikes)s, %(created_at)s)
                ON CONFLICT (post_id) DO UPDATE SET
                    title    = EXCLUDED.title,
                    content  = EXCLUDED.content,
                    views    = EXCLUDED.views,
                    likes    = EXCLUDED.likes,
                    dislikes = EXCLUDED.dislikes,
                    collected_at = NOW()
            """, post)

            # 댓글 UPSERT
            for comment in post.get("comments", []):
                cur.execute("""
                    INSERT INTO comments (comment_id, post_id, author, content, likes, dislikes, created_at)
                    VALUES (%(comment_id)s, %(post_id)s, %(author)s, %(content)s, %(likes)s, %(dislikes)s, %(created_at)s)
                    ON CONFLICT (comment_id) DO UPDATE SET
                        content  = EXCLUDED.content,
                        likes    = EXCLUDED.likes,
                        dislikes = EXCLUDED.dislikes,
                        collected_at = NOW()
                """, comment)

        self.conn.commit()
        cur.close()

    def save_stocks(self, stocks):
        """종목 마스터 UPSERT"""
        cur = self.conn.cursor()

        # 기존 종목 비활성화 후 수집된 종목만 활성화 (순위 밖으로 밀린 종목 처리)
        cur.execute("UPDATE stocks SET is_active = FALSE")

        for stock in stocks:
            cur.execute("""
                INSERT INTO stocks (stock_code, name, market, market_cap, rank, is_active, updated_at)
                VALUES (%(stock_code)s, %(name)s, %(market)s, %(market_cap)s, %(rank)s, TRUE, NOW())
                ON CONFLICT (stock_code) DO UPDATE SET
                    name       = EXCLUDED.name,
                    market     = EXCLUDED.market,
                    market_cap = EXCLUDED.market_cap,
                    rank       = EXCLUDED.rank,
                    is_active  = TRUE,
                    updated_at = NOW()
            """, stock)

        self.conn.commit()
        cur.close()

    def save_themes(self, themes, stock_themes):
        """테마 + 종목-테마 매핑 저장"""
        cur = self.conn.cursor()

        for theme in themes:
            cur.execute("""
                INSERT INTO themes (theme_code, theme_name, updated_at)
                VALUES (%(theme_code)s, %(theme_name)s, NOW())
                ON CONFLICT (theme_code) DO UPDATE SET
                    theme_name = EXCLUDED.theme_name,
                    updated_at = NOW()
            """, theme)

        # 매핑 초기화 후 재삽입
        cur.execute("DELETE FROM stock_themes")
        for mapping in stock_themes:
            # stocks 테이블에 존재하는 종목만 삽입 (FK 제약)
            cur.execute("""
                INSERT INTO stock_themes (stock_code, theme_code)
                SELECT %(stock_code)s, %(theme_code)s
                WHERE EXISTS (SELECT 1 FROM stocks WHERE stock_code = %(stock_code)s)
                ON CONFLICT DO NOTHING
            """, mapping)

        self.conn.commit()
        cur.close()

    def get_active_stocks(self):
        """활성 종목 코드 목록 조회 (DAG에서 사용)"""
        cur = self.conn.cursor()
        cur.execute("SELECT stock_code FROM stocks WHERE is_active = TRUE ORDER BY rank")
        codes = [row[0] for row in cur.fetchall()]
        cur.close()
        return codes

    def get_known_post_ids(self, stock_code, limit=200):
        """최근 게시글 ID 목록 조회 (누락 방지 비교용)"""
        cur = self.conn.cursor()
        cur.execute(
            "SELECT post_id FROM posts WHERE stock_code = %s ORDER BY collected_at DESC LIMIT %s",
            (stock_code, limit)
        )
        ids = {str(row[0]) for row in cur.fetchall()}
        cur.close()
        return ids

    def close(self):
        self.conn.close()