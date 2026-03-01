import os

from dotenv import load_dotenv

from market_insight.crawlers.base import BaseCrawler

load_dotenv()


class PublicDataPriceCrawler(BaseCrawler):
    """공공데이터포털 금융위원회 주식시세정보 API를 통한 일별 시세 수집"""

    BASE_URL = "https://apis.data.go.kr/1160100/service/GetStockSecuritiesInfoService/getStockPriceInfo"

    def __init__(self):
        super().__init__()
        self.api_key = os.getenv("DATA_GO_KR_API_KEY")

    def crawl(self, stock_code=None, page=None):
        return self.fetch_daily_prices()

    def fetch_daily_prices(self, base_date=None):
        """해당 날짜의 전체 종목 시세를 한 번에 수집

        Args:
            base_date: 기준일자 (yyyyMMdd 형식). None이면 전일 날짜 사용.

        Returns:
            list[dict]: [{stock_code, trade_date, open_price, high_price, low_price, close_price, volume}, ...]
        """
        if base_date is None:
            from datetime import datetime, timedelta
            yesterday = datetime.now() - timedelta(days=1)
            base_date = yesterday.strftime("%Y%m%d")

        params = {
            "serviceKey": self.api_key,
            "basDt": base_date,
            "numOfRows": 10000,
            "pageNo": 1,
            "resultType": "json",
        }

        response = self.http_client.get(self.BASE_URL, params=params)
        data = response.json()

        items = data.get("response", {}).get("body", {}).get("items", {}).get("item", [])
        if not items:
            print(f"[{base_date}] 시세 데이터 없음 (주말/공휴일)")
            return []

        prices = []
        for item in items:
            prices.append({
                "stock_code": item.get("srtnCd", ""),
                "trade_date": f"{base_date[:4]}-{base_date[4:6]}-{base_date[6:8]}",
                "open_price": int(item.get("mkp", 0)),
                "high_price": int(item.get("hipr", 0)),
                "low_price": int(item.get("lopr", 0)),
                "close_price": int(item.get("clpr", 0)),
                "volume": int(item.get("trqu", 0)),
            })

        print(f"[{base_date}] {len(prices)}종목 시세 수집 완료")
        return prices