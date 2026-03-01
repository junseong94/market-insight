import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

KST = pendulum.timezone("Asia/Seoul")


def fetch_and_save_prices(**context):
    """전일 시세를 공공데이터포털 API로 수집하여 DB에 저장"""
    from datetime import datetime, timedelta

    from market_insight.crawlers.public_data_price import PublicDataPriceCrawler
    from market_insight.storage.postgres import PostgresStorage

    # 전일(D-1) 날짜로 조회 (API 데이터 갱신이 D+1 13:00 이후)
    yesterday = datetime.now() - timedelta(days=1)
    base_date = yesterday.strftime("%Y%m%d")

    crawler = PublicDataPriceCrawler()
    prices = crawler.fetch_daily_prices(base_date)

    if prices:
        storage = PostgresStorage()
        storage.save_daily_prices(prices)
        storage.close()


with DAG(
    dag_id="daily_prices",
    schedule_interval="0 18 * * 1-5",  # 평일 18:00 KST (장 마감 후)
    start_date=pendulum.datetime(2026, 3, 1, tz=KST),
    catchup=False,
    tags=["public_data", "daily_prices"],
) as dag:

    PythonOperator(
        task_id="fetch_and_save_prices",
        python_callable=fetch_and_save_prices,
    )