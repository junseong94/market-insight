import requests
import time
import random

class HttpClient:
    # 1. requests.Session 생성 (커넥션 재사용, Java의RestTemplate처럼)
    # 2. 공통 헤더 설정 (User-Agent, Referer)
    #    → 네이버는 User-Agent 없으면 차단할 수 있음
    def __init__(self): # 생성자
        self.session = requests.session() # HTTP 세션 생성
        self.session.headers.update({ # 모든 요청에 공통 헤더 적용
            "User-Agent":   "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                            "AppleWebKit/537.36 (KHTML, like Gecko) "
                            "Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://finance.naver.com",
        })

    # 1. rate limit: time.sleep(random.uniform(0.3, 0.5))
    # 2. self.session.get(url, params=params) 호출
    # 3. response 반환
    def get(self, url, params=None): # HTTP GET 요청 메서드, self = 자바의 this
        time.sleep(random.uniform(0.3, 0.5)) # 0.3 ~ 0.5초 랜덤 대기(rate limit)
        response = self.session.get(url, params=params) # GET 요청. params 는 쿼리스트링으로 자동 변환
        response.raise_for_status() # 4xx/5xx 예외 발생
        return response