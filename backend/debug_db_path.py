import os
import sqlite3
from pathlib import Path

# 현재 작업 디렉토리 확인
print(f"현재 작업 디렉토리: {os.getcwd()}")

# database.py에서 사용하는 경로 확인
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/taco_trading.db")
print(f"DATABASE_URL: {DATABASE_URL}")

# 실제 파일 경로 확인
db_path = DATABASE_URL.replace("sqlite:///", "")
print(f"실제 DB 파일 경로: {db_path}")
abs_path = os.path.abspath(db_path)
print(f"절대 경로: {abs_path}")

# 파일 존재 여부 확인
print(f"파일 존재: {os.path.exists(abs_path)}")

if os.path.exists(abs_path):
    # 데이터베이스 스키마 확인
    conn = sqlite3.connect(abs_path)
    cursor = conn.cursor()
    
    print("\n=== ETF_PRICES 테이블 스키마 ===")
    try:
        cursor.execute('PRAGMA table_info(etf_prices)')
        columns = cursor.fetchall()
        for row in columns:
            print(f"  {row[1]} ({row[2]})")
    except Exception as e:
        print(f"에러: {e}")
    
    print("\n=== 모든 테이블 목록 ===")
    try:
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        for table in tables:
            print(f"  - {table[0]}")
    except Exception as e:
        print(f"에러: {e}")
    
    conn.close()
else:
    print("데이터베이스 파일이 존재하지 않습니다!")

# 다른 가능한 위치들도 확인
possible_paths = [
    "./taco_trading.db",
    "./backend/app/taco_trading.db", 
    "./app/taco_trading.db",
    "taco_trading.db"
]

print("\n=== 다른 가능한 경로들 ===")
for path in possible_paths:
    abs_path = os.path.abspath(path)
    exists = os.path.exists(abs_path)
    print(f"{path} -> {abs_path} (존재: {exists})") 