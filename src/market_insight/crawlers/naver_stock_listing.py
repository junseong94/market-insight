from bs4 import BeautifulSoup
from market_insight.crawlers.base import BaseCrawler


class NaverStockListingCrawler(BaseCrawler):
    """네이버 증권 시가총액 페이지에서 종목 리스트 수집"""

    def crawl(self, stock_code=None, page=None):
        # BaseCrawler 인터페이스 맞추기용, 실제로는 crawl_top_stocks 사용
        return self.crawl_top_stocks()

    def crawl_top_stocks(self, limit=500):
        """KOSPI + KOSDAQ 시총 상위 종목 수집 (통합 시총 순위)"""
        all_stocks = []

        # 양쪽 시장에서 충분히 수집 (각 시장 시총순 정렬이므로 넉넉히)
        for market_code, market_name in [("0", "KOSPI"), ("1", "KOSDAQ")]:
            page = 1
            while len([s for s in all_stocks if s["market"] == market_name]) < limit:
                page_stocks = self._fetch_page(market_code, market_name, page)
                if not page_stocks:
                    break
                all_stocks.extend(page_stocks)
                page += 1

        # 시총 기준 통합 정렬 후 상위 N개
        all_stocks.sort(key=lambda s: s["market_cap"], reverse=True)
        stocks = all_stocks[:limit]

        for i, stock in enumerate(stocks):
            stock["rank"] = i + 1

        return stocks

    def _fetch_page(self, market_code, market_name, page):
        """시가총액 순위 페이지 1개 파싱"""
        url = "https://finance.naver.com/sise/sise_market_sum.naver"
        params = {"sosok": market_code, "page": page}
        response = self.http_client.get(url, params=params)

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("table.type_2")
        if not table:
            return []

        stocks = []
        for row in table.select("tr"):
            cells = row.select("td")
            if len(cells) < 7:
                continue

            link = cells[1].select_one("a")
            if not link or "code=" not in link.get("href", ""):
                continue

            code = link["href"].split("code=")[1]
            name = link.get_text(strip=True)
            market_cap_text = cells[6].get_text(strip=True).replace(",", "")

            stocks.append({
                "stock_code": code,
                "name": name,
                "market": market_name,
                "market_cap": int(market_cap_text) if market_cap_text.isdigit() else 0,
            })

        return stocks