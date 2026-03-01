# Market Insight

한국 주식 시장 데이터 수집/분석 플랫폼

네이버 종목토론방, DART 공시, 시세 데이터 등을 수집하여 자체 데이터 웨어하우스를 구축하고, 종목별 관심도/투자심리를 분석하는 프로젝트입니다.

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.14+ |
| 패키지 관리 | Poetry |
| 데이터 수집 | requests + BeautifulSoup |
| 오케스트레이션 | Apache Airflow (예정) |
| 저장소 | PostgreSQL (DW), MinIO + Parquet (데이터레이크) |
| 분석 | DuckDB, dbt (예정) |
| 서빙 | FastAPI + Metabase (예정) |

## 프로젝트 구조

```
market-insight/
├── pyproject.toml
├── src/
│   └── market_insight/
│       ├── crawlers/          # 데이터 수집기
│       │   ├── base.py        # 크롤러 추상 클래스
│       │   └── naver_discussion.py  # 네이버 종목토론방 크롤러
│       ├── storage/           # 저장 레이어
│       ├── models/            # DB 스키마/ORM
│       └── utils/
│           └── http_client.py # HTTP 클라이언트 (세션 관리, rate limiting)
├── scripts/
│   └── test_crawl.py          # 크롤러 테스트 스크립트
└── tests/
```

## 현재 구현 상태

### Phase 1: 네이버 종목토론방 크롤러 (진행중)

#### 수집 데이터

종목토론방에서 **게시글 목록 + 본문 + 댓글**을 수집합니다.

```
crawl("005930", page=1)
├── 게시글 목록 (HTML 파싱)
│   → 제목, 작성자, 날짜, 조회수, 공감/비공감
├── 게시글 본문 (Next.js SSR 데이터 추출)
│   → 본문 텍스트
└── 댓글 (JSONP API)
    → 댓글 내용, 작성자, 공감/비공감
```

#### 데이터 흐름

| 단계 | URL | 방식 |
|------|-----|------|
| 목록 | `finance.naver.com/item/board.naver` | HTML 테이블 파싱 |
| 본문 | `m.stock.naver.com/pc/domestic/stock/{code}/discussion/{nid}` | `__NEXT_DATA__` JSON에서 `contentHtml` 추출 |
| 댓글 | `apis.naver.com/commentBox/cbox/web_naver_list_jsonp.json` | JSONP 응답 파싱 |

## 로드맵

- [x] Phase 1-1: 네이버 종목토론방 크롤러 구현
- [ ] Phase 1-2: PostgreSQL 저장 레이어
- [ ] Phase 1-3: Airflow DAG 파이프라인
- [ ] Phase 2: 과거 데이터 백필 + 대용량 처리 (DuckDB/Spark)
- [ ] Phase 3: dbt 변환 + FastAPI/Metabase 서빙
- [ ] Phase 4: 운영 안정화 + 추가 데이터소스 (DART 공시 등)

## 실행 방법

```bash
# 의존성 설치
poetry install

# 크롤러 테스트 (삼성전자 종목토론방 1페이지)
poetry run python scripts/test_crawl.py
```

## 배치 스케줄 (목표)

- 평일 08:00, 13:00, 18:00 (하루 3회)
- 상위 500종목, 종목당 5페이지 (100건)
- 목표 데이터량: 500MB+/일