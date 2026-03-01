from abc import ABC, abstractmethod # 추상 클래스 도구

from market_insight.utils.http_client import HttpClient


class BaseCrawler(ABC):
    def __init__(self):
        self.http_client = HttpClient()

    @abstractmethod
    def crawl(self, stock_code, page):
        pass
