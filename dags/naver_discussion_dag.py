import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

KST = pendulum.timezone("Asia/Seoul")

# 크롤링할 종목 리스트 (Phase 1에서는 소수 종목으로 테스트)
STOCK_CODES = ["005930", "000660", "373220"]  # 삼성전자, SK하이닉스, LG에너지솔루션
PAGES_PER_STOCK = 1  # 종목당 수집 페이지 수


def crawl_and_save(stock_code, pages):
    """종목 하나를 크롤링해서 DB에 저장"""
    from market_insight.crawlers.naver_discussion import NaverDiscussionCrawler
    from market_insight.storage.postgres import PostgresStorage

    crawler = NaverDiscussionCrawler()
    storage = PostgresStorage()

    total = 0
    for page in range(1, pages + 1):
        posts = crawler.crawl(stock_code, page=page)
        storage.save_posts(posts)
        total += len(posts)

    storage.close()
    print(f"[{stock_code}] {total}건 저장 완료")


# DAG 정의
# schedule: 평일(월~금) 08:00, 13:00, 18:00 KST
# cron 3개를 하나로 못 묶으므로 DAG 3개 생성
for hour in [8, 13, 18]:
    dag_id = f"naver_discussion_{hour:02d}h"

    with DAG(
        dag_id=dag_id,
        # 분 시 일 월 요일(1-5 = 월~금), KST 기준
        schedule_interval=f"0 {hour} * * 1-5",
        start_date=pendulum.datetime(2026, 3, 1, tz=KST),
        catchup=False,  # 과거 미실행분 소급 실행 안 함
        tags=["naver", "discussion"],
    ) as dag:

        for stock_code in STOCK_CODES:
            PythonOperator(
                task_id=f"crawl_{stock_code}",
                python_callable=crawl_and_save,
                op_kwargs={"stock_code": stock_code, "pages": PAGES_PER_STOCK},
            )

        # globals()에 등록해야 Airflow가 인식
        globals()[dag_id] = dag