import sqlite3

conn = sqlite3.connect('app/taco_trading.db')
cursor = conn.cursor()

print("=== ETF_PRICES 테이블 스키마 ===")
cursor.execute('PRAGMA table_info(etf_prices)')
columns = cursor.fetchall()
for row in columns:
    print(f"컬럼: {row[1]} ({row[2]})")

print("\n=== ETF_PRICES 테이블 데이터 샘플 ===")
cursor.execute('SELECT * FROM etf_prices LIMIT 3')
data = cursor.fetchall()
for row in data:
    print(row)

conn.close() 