from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "sqlite:///./app/taco_trading.db" # os.getenv("DATABASE_URL", "sqlite:///./app/taco_trading.db")

# 디버깅: 실제 사용되는 데이터베이스 파일 경로 출력
print(f"=== 데이터베이스 디버깅 ===")
print(f"현재 작업 디렉토리: {os.getcwd()}")
print(f"DATABASE_URL: {DATABASE_URL}")
db_file_path = DATABASE_URL.replace("sqlite:///", "")
abs_db_path = os.path.abspath(db_file_path)
print(f"실제 DB 파일 경로: {abs_db_path}")
print(f"DB 파일 존재: {os.path.exists(abs_db_path)}")
print("==========================")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)