from bs4 import BeautifulSoup
from market_insight.crawlers.base import BaseCrawler


class NaverThemeCrawler(BaseCrawler):
    """네이버 증권 테마 페이지에서 테마 목록 + 종목-테마 매핑 수집"""

    def crawl(self, stock_code=None, page=None):
        return self.crawl_themes()

    def crawl_themes(self):
        """전체 테마 목록 + 테마별 소속 종목 수집"""
        themes = []
        stock_themes = []  # [{stock_code, theme_code}, ...]

        # 1) 테마 목록 수집 (전체 페이지 순회)
        theme_list = self._fetch_theme_list()

        # 2) 각 테마의 소속 종목 수집
        for theme in theme_list:
            themes.append(theme)
            members = self._fetch_theme_members(theme["theme_code"])

            for stock_code in members:
                stock_themes.append({
                    "stock_code": stock_code,
                    "theme_code": theme["theme_code"],
                })

        return {"themes": themes, "stock_themes": stock_themes}

    def _fetch_theme_list(self):
        """테마 목록 전체 페이지 수집"""
        url = "https://finance.naver.com/sise/theme.naver"
        themes = []

        for page in range(1, 20):  # 최대 20페이지
            response = self.http_client.get(url, params={"page": page})
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.select("td a[href*='no=']")

            if not links:
                break

            for link in links:
                href = link.get("href", "")
                if "no=" not in href:
                    continue
                theme_code = href.split("no=")[1].split("&")[0]
                theme_name = link.get_text(strip=True)
                themes.append({
                    "theme_code": theme_code,
                    "theme_name": theme_name,
                })

        return themes

    def _fetch_theme_members(self, theme_code):
        """테마에 속한 종목 코드 목록 수집"""
        url = "https://finance.naver.com/sise/sise_group_detail.naver"
        params = {"type": "theme", "no": theme_code}
        response = self.http_client.get(url, params=params)

        soup = BeautifulSoup(response.text, "html.parser")
        table = soup.select_one("table.type_5")
        if not table:
            return []

        codes = []
        for row in table.select("tr"):
            cells = row.select("td")
            if len(cells) < 2:
                continue
            link = cells[0].select_one("a[href*='code=']")
            if link:
                code = link["href"].split("code=")[1]
                codes.append(code)

        return codes