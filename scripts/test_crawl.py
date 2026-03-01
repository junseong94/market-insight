from market_insight.crawlers.naver_discussion import NaverDiscussionCrawler

crawler = NaverDiscussionCrawler()
posts = crawler.crawl("005930", page=1)

for i, post in enumerate(posts[:3]):  # 상위 3개만 출력
    print(f"\n===== 게시글 {i + 1} =====")
    print(f"제목: {post['title']}")
    print(f"작성자: {post['author']}")
    print(f"날짜: {post['created_at']}")
    print(f"조회: {post['views']} | 공감: {post['likes']} | 비공감: {post['dislikes']}")
    print(f"본문: {post['content'][:100]}...")
    print(f"댓글 수: {len(post['comments'])}")

    for c in post["comments"][:2]:  # 댓글 2개만
        print(f"  - {c['author']}: {c['content'][:50]}")
