# Market Insight

한국 주식 시장 데이터 수집/분석 플랫폼 (사이드 프로젝트)

## 프로젝트 목적
- 네이버 종목토론방, DART 공시, 시세 데이터 등을 수집하여 자체 DW 구축
- 대용량 데이터 처리 경험 확보 (Airflow, Spark, Parquet)
- 수집 데이터 기반 종목 관심도/심리 분석 서비스 제공

## 기술 스택
- **언어**: Python 3.14+
- **패키지 관리**: Poetry
- **수집**: requests + BeautifulSoup (크롤링), 공식 API (DART 등)
- **오케스트레이션**: Apache Airflow (Docker Compose, LocalExecutor)
- **저장**: PostgreSQL (DW), MinIO (S3 호환 데이터레이크), Parquet 포맷
- **분석**: DuckDB (대용량 집계, 데이터 커지면 도입), dbt (변환)
- **서빙**: FastAPI + Metabase (추후)

## 프로젝트 구조
```
market-insight/
├── docker-compose.yml        # Airflow + PostgreSQL + MinIO
├── pyproject.toml
├── .env                      # 환경변수 (git-ignored)
├── src/
│   └── market_insight/
│       ├── crawlers/         # 데이터 수집기 (소스별 모듈)
│       ├── storage/          # 저장 레이어 (PostgreSQL, Parquet/MinIO)
│       ├── models/           # DB 스키마/ORM 모델
│       └── utils/            # 유틸리티 (rate limiter, http client 등)
├── dags/                     # Airflow DAG 파일
├── tests/
└── scripts/                  # DB 초기화 등 스크립트
```

## 구현 단계
- Phase 1: 네이버 종목토론방 크롤러 + Airflow 파이프라인 (현재)
- Phase 2: 과거 데이터 백필 + DuckDB/Spark 대용량 처리
- Phase 3: dbt 변환 + FastAPI/Metabase 서빙
- Phase 4: 운영 안정화 + 추가 데이터소스

## 배치 스케줄
- 평일 08:00, 13:00, 18:00 (하루 3회)
- 종목토론방: 상위 500종목, 종목당 5페이지(100건)
- 목표 데이터량: 500MB+/일

## 컨벤션
- 크롤러는 `crawlers/base.py`의 BaseCrawler를 상속하여 구현
- 멱등성 필수: post_id 기준 UPSERT (INSERT ON CONFLICT)
- rate limiting: 요청 간 0.3~0.5초 딜레이
- raw 데이터는 Parquet로 MinIO에 보관 (데이터레이크)
- 정제 데이터는 PostgreSQL에 적재 (DW)
