import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

KST = pendulum.timezone("Asia/Seoul")


def update_stock_listing():
    """시총 상위 500종목 수집 → DB 저장"""
    from market_insight.crawlers.naver_stock_listing import NaverStockListingCrawler
    from market_insight.storage.postgres import PostgresStorage

    crawler = NaverStockListingCrawler()
    stocks = crawler.crawl_top_stocks(limit=500)

    storage = PostgresStorage()
    storage.save_stocks(stocks)
    storage.close()

    kospi = len([s for s in stocks if s["market"] == "KOSPI"])
    kosdaq = len([s for s in stocks if s["market"] == "KOSDAQ"])
    print(f"종목 업데이트 완료: {len(stocks)}종목 (KOSPI: {kospi}, KOSDAQ: {kosdaq})")


def update_themes():
    """테마 목록 + 종목-테마 매핑 수집 → DB 저장"""
    from market_insight.crawlers.naver_theme import NaverThemeCrawler
    from market_insight.storage.postgres import PostgresStorage

    crawler = NaverThemeCrawler()
    result = crawler.crawl_themes()

    storage = PostgresStorage()
    storage.save_themes(result["themes"], result["stock_themes"])
    storage.close()

    print(f"테마 업데이트 완료: {len(result['themes'])}테마, {len(result['stock_themes'])}매핑")


with DAG(
    dag_id="stock_listing_update",
    schedule_interval="0 6 * * *",  # 매일 06:00 KST
    start_date=pendulum.datetime(2026, 3, 1, tz=KST),
    catchup=False,
    tags=["naver", "stock_listing"],
) as dag:

    task_stocks = PythonOperator(
        task_id="update_stock_listing",
        python_callable=update_stock_listing,
    )

    task_themes = PythonOperator(
        task_id="update_themes",
        python_callable=update_themes,
    )

    # 종목 먼저 저장 → 테마 매핑 (FK 제약 때문)
    task_stocks >> task_themes