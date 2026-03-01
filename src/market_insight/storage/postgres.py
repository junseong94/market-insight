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

    def close(self):
        self.conn.close()