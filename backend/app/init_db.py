import os
import sys
from pathlib import Path

# 현재 파일의 디렉토리를 얻습니다
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent

# Python 경로에 backend 디렉토리 추가
sys.path.append(str(backend_dir))

from app.database import Base, engine
from app.model import TrumpStatement, TACOSignal, ETFPrice

def init_db():
    print("데이터베이스 테이블 생성 시작...")
    try:
        # 기존 테이블 삭제 (필요한 경우)
        Base.metadata.drop_all(bind=engine)
        print("기존 테이블 삭제 완료")
        
        # 새 테이블 생성
        Base.metadata.create_all(bind=engine)
        print("새 테이블 생성 완료")
        
    except Exception as e:
        print(f"데이터베이스 초기화 중 오류 발생: {str(e)}")
        raise e

if __name__ == "__main__":
    init_db()
