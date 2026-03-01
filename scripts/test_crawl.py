from market_insight.crawlers.naver_discussion import NaverDiscussionCrawler
from market_insight.storage.postgres import PostgresStorage

# 1. 크롤링
crawler = NaverDiscussionCrawler()
posts = crawler.crawl("005930", page=1)
print(f"수집 완료: {len(posts)}건")

# 2. DB 저장
storage = PostgresStorage()
storage.save_posts(posts)
storage.close()
print("DB 저장 완료")

# 3. 결과 출력 (상위 3개)
for i, post in enumerate(posts[:3]):
    print(f"\n===== 게시글 {i + 1} =====")
    print(f"제목: {post['title']}")
    print(f"작성자: {post['author']}")
    print(f"본문: {post['content'][:100]}...")
    print(f"댓글 수: {len(post['comments'])}")