import os
from dotenv import load_dotenv

load_dotenv()  # .env 파일 로드

# .env에서 DB 접속 정보 가져오기 (Java의 application.properties 역할)
DB_CONFIG = {
    "host": os.getenv("POSTGRES_HOST", "localhost"),
    "port": int(os.getenv("POSTGRES_PORT", "5433")),
    "dbname": os.getenv("POSTGRES_DB", "market_insight"),
    "user": os.getenv("POSTGRES_USER", "market"),
    "password": os.getenv("POSTGRES_PASSWORD", "market1234"),
}