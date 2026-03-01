# Market Insight

한국 주식 시장 데이터 수집/분석 플랫폼

네이버 종목토론방, DART 공시, 시세 데이터 등을 수집하여 자체 데이터 웨어하우스를 구축하고, 종목별 관심도/투자심리를 분석하는 프로젝트입니다.

## 기술 스택

| 구분 | 기술 |
|------|------|
| 언어 | Python 3.14+ |
| 패키지 관리 | Poetry |
| 데이터 수집 | requests + BeautifulSoup |
| 오케스트레이션 | Apache Airflow 2.10 (Docker Compose, LocalExecutor) |
| 저장소 | PostgreSQL 17 (DW) |
| 컨테이너 | Docker Compose |
| 분석 | DuckDB, dbt (예정) |
| 서빙 | FastAPI + Metabase (예정) |

## 프로젝트 구조

```
market-insight/
├── docker-compose.yml              # PostgreSQL + Airflow 인프라
├── docker/
│   └── init-db.sql                 # DB 초기화 (market_insight + airflow DB 분리)
├── pyproject.toml
├── .env                            # DB 접속 정보 (git-ignored)
├── dags/
│   ├── naver_discussion_dag.py     # 종목토론방 크롤링 DAG (매시간)
│   └── stock_listing_dag.py        # 종목/테마 업데이트 DAG (매일)
├── src/
│   └── market_insight/
│       ├── crawlers/
│       │   ├── base.py             # 크롤러 추상 클래스 (BaseCrawler)
│       │   ├── naver_discussion.py # 종목토론방 크롤러 (목록+본문+댓글)
│       │   ├── naver_stock_listing.py  # 시총 상위 종목 크롤러
│       │   └── naver_theme.py      # 테마/섹터 크롤러
│       ├── storage/
│       │   └── postgres.py         # PostgreSQL 저장 (psycopg2 raw SQL)
│       ├── models/
│       └── utils/
│           ├── http_client.py      # HTTP 클라이언트 (세션, rate limiting)
│           └── db_config.py        # DB 접속 설정 (.env 로드)
├── scripts/
│   ├── init_db.py                  # 테이블 생성 스크립트
│   └── test_crawl.py               # E2E 테스트 스크립트
└── tests/
```

## 인프라 구성

Docker Compose로 전체 인프라를 관리합니다.

```
┌────────────────────────────────────────────────────┐
│  Docker Compose                                    │
│                                                    │
│  ┌──────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │PostgreSQL │  │   Airflow    │  │   Airflow    │ │
│  │  :5433    │  │  Webserver   │  │  Scheduler   │ │
│  │           │  │   :8080      │  │              │ │
│  │ market_   │  └──────┬───────┘  └──────┬───────┘ │
│  │ insight DB│         │                 │         │
│  │ airflow DB│◄────────┴─────────────────┘         │
│  └──────────┘                                      │
└────────────────────────────────────────────────────┘
```

| 서비스 | 포트 | 용도 |
|--------|------|------|
| PostgreSQL | 5433 | 앱 데이터 (`market_insight` DB) + Airflow 메타 (`airflow` DB) |
| Airflow Webserver | 8080 | 모니터링 UI (admin/admin) |
| Airflow Scheduler | - | DAG 스케줄 실행 |

## DB 스키마

```
market_insight DB
─────────────────
stocks          종목 마스터 (시총 상위 500, KOSPI+KOSDAQ)
themes          테마 목록 (500+개)
stock_themes    종목-테마 N:N 매핑
posts           종목토론방 게시글
comments        게시글 댓글
```

## 데이터 수집 파이프라인

### 1. 종목/테마 업데이트 (`stock_listing_update` DAG)

매일 평일 06:00 KST에 실행. 장 시작 전 종목 마스터를 갱신합니다.

```
update_stock_listing ──→ update_themes
        │                      │
        ▼                      ▼
  네이버 시총 순위 크롤링    네이버 테마 페이지 크롤링
  KOSPI+KOSDAQ 통합 정렬    500개 테마 + 소속 종목
  상위 500종목 UPSERT       테마/매핑 UPSERT
```

| 데이터 소스 | URL | 수집 내용 |
|-------------|-----|-----------|
| 시총 순위 | `finance.naver.com/sise/sise_market_sum.naver` | 종목코드, 이름, 시장, 시가총액 |
| 테마 목록 | `finance.naver.com/sise/theme.naver` | 테마코드, 테마명 |
| 테마 상세 | `finance.naver.com/sise/sise_group_detail.naver` | 테마별 소속 종목 |

### 2. 종목토론방 크롤링 (`naver_discussion` DAG)

평일 매시간 실행. DB에서 활성 종목 500개를 읽어 토론방을 수집합니다.

```
crawl_all_stocks
    │
    ├─ stocks 테이블에서 활성 종목 조회
    │
    └─ 각 종목별:
        ├─ 목록: finance.naver.com/item/board.naver (HTML)
        ├─ 본문: m.stock.naver.com/.../{code}/discussion/{nid} (__NEXT_DATA__)
        └─ 댓글: apis.naver.com/commentBox/cbox/... (JSONP)
```

| 수집 항목 | 필드 |
|-----------|------|
| 게시글 | post_id, 제목, 본문, 작성자, 날짜, 조회수, 공감/비공감 |
| 댓글 | comment_id, 내용, 작성자, 공감/비공감, 날짜 |

> **누락 방지**: 이전 수집분과 겹칠 때까지 페이지를 순회합니다 (최대 10페이지). DB에 이미 있는 post_id와 비교하여 새 게시글만 본문/댓글을 수집하므로 HTTP 요청을 절약합니다. UPSERT로 중복도 방지됩니다.

## 로드맵

- [x] Phase 1-1: 네이버 종목토론방 크롤러 구현
- [x] Phase 1-2: PostgreSQL 저장 레이어 (psycopg2 raw SQL, UPSERT)
- [x] Phase 1-3: Airflow DAG 파이프라인
- [x] Phase 2-1: 종목 마스터 자동 수집 (시총 상위 500종목)
- [x] Phase 2-2: 테마/섹터 분류 수집 (500개 테마, 9,000+ 매핑)
- [x] Phase 2-3: DAG 매시간 스케줄 + 동적 종목 조회
- [x] 게시글 누락 방지 (페이지 순회 + post_id 비교)
- [ ] 과거 데이터 백필 + 대용량 처리 (DuckDB/Spark)
- [ ] dbt 변환 + FastAPI/Metabase 서빙
- [ ] 운영 안정화 + 추가 데이터소스 (DART 공시 등)

## 실행 방법

```bash
# 1. 인프라 기동
docker compose up -d

# 2. 의존성 설치
poetry install

# 3. 테이블 생성
poetry run python scripts/init_db.py

# 4. 종목 마스터 수집 (최초 1회)
poetry run python -c "
from market_insight.crawlers.naver_stock_listing import NaverStockListingCrawler
from market_insight.storage.postgres import PostgresStorage
crawler = NaverStockListingCrawler()
stocks = crawler.crawl_top_stocks(limit=500)
storage = PostgresStorage()
storage.save_stocks(stocks)
storage.close()
print(f'{len(stocks)}종목 저장 완료')
"

# 5. 크롤러 테스트
poetry run python scripts/test_crawl.py

# 6. Airflow UI 확인
# http://localhost:8080 (admin / admin)
```