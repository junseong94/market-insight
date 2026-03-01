import json

from bs4 import BeautifulSoup # HTTP 파싱
from market_insight.crawlers.base import BaseCrawler

#  5. 로직 흐름
#
#   crawl("005930", page=1)
#   │
#   ├─ 1) _fetch_post_list("005930", 1)
#   │     목록 페이지 HTML 요청 → 파싱
#   │     → posts = [{post_id, title, author, ...}, {...}, ...]
#   │
#   ├─ 2) 각 post마다 반복:
#   │     │
#   │     ├─ _fetch_post_detail("005930", post_id) : 게시글 상세 추출
#   │     │   상세 페이지 HTML 요청 → 본문 추출
#   │     │   → post["content"] = "본문 내용..."
#   │     │
#   │     └─ _fetch_comments(post_id) : 게시글의 댓글 추출
#   │         댓글 API(JSONP) 요청 → JSON 파싱
#   │         → post["comments"] = [{comment_id, author, content, ...}, ...]
#   │
#   └─ 3) return posts (전체 결과 반환)
class NaverDiscussionCrawler(BaseCrawler):
    def crawl(self, stock_code, page=1):
        posts = self._fetch_post_list(stock_code, page)
        for post in posts:
            post["content"] = self._fetch_post_detail(stock_code, post["post_id"])
            post["comments"] = self._fetch_comments(post["post_id"])
        return posts

    def crawl_until_caught_up(self, stock_code, known_post_ids=None, max_pages=10):
        """페이지를 순회하며 새 게시글을 모두 수집 (이전 수집분과 겹칠 때까지)

        - known_post_ids: DB에 이미 존재하는 post_id 집합
        - max_pages: 안전 장치 (최대 페이지 수)
        - 이미 수집한 게시글은 본문/댓글 요청을 건너뛰어 HTTP 요청 절약
        """
        if known_post_ids is None:
            known_post_ids = set()

        all_posts = []

        for page in range(1, max_pages + 1):
            page_posts = self._fetch_post_list(stock_code, page)
            if not page_posts:
                break

            # post_id가 유효한 게시글만 필터
            valid_posts = [p for p in page_posts if p.get("post_id")]

            # 새 게시글만 본문+댓글 수집 (HTTP 요청 절약)
            new_posts = [p for p in valid_posts if p["post_id"] not in known_post_ids]

            for post in new_posts:
                post["content"] = self._fetch_post_detail(stock_code, post["post_id"])
                post["comments"] = self._fetch_comments(post["post_id"])

            all_posts.extend(new_posts)

            # 이 페이지에 이미 수집한 게시글이 있으면 → 이전 수집분과 겹침, 중단
            if len(new_posts) < len(valid_posts):
                break

        return all_posts

    def _fetch_post_list(self, stock_code, page):
        url = "https://finance.naver.com/item/board.naver"
        params = {"code": stock_code, "page": page}
        response = self.http_client.get(url, params=params)

        soup = BeautifulSoup(response.text, "html.parser")
        rows = soup.select("table.type2 tr") # CSS 셀렉터로 요소 선택

        posts = []
        for row in rows:
            cells = row.select("td")

            # 목록 테이블에서 수집 필드가 6개(날짜, 제목, 작성자, 조회, 공감, 비공감)
            # cells가 6개 미만이면 헤더행 or 빈행으로 스킵 => 실제 페이지 칼럼수가 다르면 조정해야함
            if len(cells) < 6:
                continue

            posts.append({
                "stock_code": stock_code,
                "post_id": self._extract_post_id(cells[1]),
                "title": cells[1].get_text(strip=True), # get_text()태그 안 텍스트만 추출
                "author": cells[2].get_text(strip=True), # strip=True: 앞뒤 공백/줄바꿈 제거 옵션
                "created_at": cells[0].get_text(strip=True),
                "views": int(cells[3].get_text(strip=True)),
                "likes": int(cells[4].get_text(strip=True)),
                "dislikes": int(cells[5].get_text(strip=True)),
            })
        return posts

    def _extract_post_id(self, cell):
        link = cell.select_one("a")
        if link and "nid=" in link.get("href", ""):
            return link["href"].split("nid=")[1].split("&")[0]
        return None

    # 상세 페이지 (본문)
    # board_read.naver → iframe(m.stock.naver.com) → __NEXT_DATA__ → contentHtml
    def _fetch_post_detail(self, stock_code, post_id):
        url = f"https://m.stock.naver.com/pc/domestic/stock/{stock_code}/discussion/{post_id}"
        response = self.http_client.get(url)

        soup = BeautifulSoup(response.text, "html.parser")
        script_tag = soup.select_one("script#__NEXT_DATA__")

        if not script_tag:
            return ""

        data = json.loads(script_tag.string)
        try:
            detail = data["props"]["pageProps"]["dehydratedState"]["queries"][1]["state"]["data"]["result"]
            content_html = detail.get("contentHtml", "")
            content_soup = BeautifulSoup(content_html, "html.parser")
            return content_soup.get_text(strip=True)
        except (KeyError, IndexError):
            return ""

    # 댓글 API
    def _fetch_comments(self, post_id):
        url = "https://apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json"
        params = {
            "ticket": "finance",
            "templateId": "community",
            "pool": "cbox12",
            "objectId": post_id,
            "pageSize": 100,
            "page": 1,
            "sort": "NEW",
            "lang": "ko",
            "country": "KR"
        }
        response = self.http_client.get(url, params=params)

        # JSONP 응답에서 JSON 추출: jQuery...({...}) -> {...}
        # JSONP: jQuery12345({"name": "홍길동", "age": 30}) 같이 콜백함수로 래핑
        # CORS 우회하기위한 옛날 방식
        text = response.text
        json_str = text[text.index("(") + 1: text.rindex(")")] # JSONP 래핑 제거. 문자열 슬라이싱

        data = json.loads(json_str) # JSON 문자열 -> 파이썬 dictionary로 변환

        comments = []
        for item in data.get("result", {}).get("commentList", []):
            comments.append({
                "comment_id": item["commentNo"],
                "post_id": post_id,
                "author": item["userName"],
                "content": item["contents"],
                "likes": item["sympathyCount"],
                "dislikes": item["antipathyCount"],
                "created_at": item["regTime"],
            })
        return comments