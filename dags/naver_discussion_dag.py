import pendulum
from airflow import DAG
from airflow.operators.python import PythonOperator

KST = pendulum.timezone("Asia/Seoul")
PAGES_PER_STOCK = 1


def get_stock_codes():
    """DB에서 활성 종목 코드 목록 조회"""
    from market_insight.storage.postgres import PostgresStorage

    storage = PostgresStorage()
    codes = storage.get_active_stocks()
    storage.close()
    return codes


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


def crawl_all_stocks(**context):
    """전체 활성 종목 순회하며 크롤링"""
    codes = get_stock_codes()
    print(f"크롤링 대상: {len(codes)}종목")

    for code in codes:
        crawl_and_save(code, PAGES_PER_STOCK)

    print(f"전체 완료: {len(codes)}종목")


with DAG(
    dag_id="naver_discussion",
    schedule_interval="0 * * * 1-5",  # 평일 매시간
    start_date=pendulum.datetime(2026, 3, 1, tz=KST),
    catchup=False,
    tags=["naver", "discussion"],
) as dag:

    PythonOperator(
        task_id="crawl_all_stocks",
        python_callable=crawl_all_stocks,
    )