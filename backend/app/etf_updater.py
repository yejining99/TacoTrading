# backend/app/etf_updater.py

import yfinance as yf
import sys
import os
import sqlite3
from pathlib import Path
from datetime import datetime
import logging
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

# 경로 설정
current_dir = Path(__file__).resolve().parent
backend_dir = current_dir.parent
sys.path.append(str(backend_dir))

from app.database import Base, engine, get_db
from app.model import ETFPrice

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ETFPriceUpdater:
    def __init__(self):
        # 트럼프 관련 미국 + 한국 ETF들
        self.etf_symbols = {
            # === 미국 ETF ===
            # 주요 지수 ETF
            'SPY': 'S&P 500 ETF',
            'QQQ': 'NASDAQ 100 ETF', 
            'DIA': 'Dow Jones ETF',
            'IWM': '러셀 2000 소형주 ETF',
            'VTI': '전체 주식시장 ETF',
            
            # 금융 섹터 (트럼프 정책에 민감)
            'XLF': '금융 섹터 ETF',
            'KBE': '은행업 ETF',
            'KRE': '지역은행 ETF',
            
            # 에너지 섹터 (석유, 가스 정책)
            'XLE': '에너지 섹터 ETF',
            'XOP': '석유가스 탐사개발 ETF',
            'USO': '원유 ETF',
            
            # 기술 섹터 (규제 정책 영향)
            'XLK': '기술 섹터 ETF',
            'SOXX': '반도체 ETF',
            'ARKK': '혁신기술 ETF',
            
            # 헬스케어 (의료정책)
            'XLV': '헬스케어 섹터 ETF',
            'IBB': '바이오테크 ETF',
            
            # 인프라/산업 (인프라 정책)
            'XLI': '산업 섹터 ETF',
            'IYT': '교통 ETF',
            'ITB': '건설 ETF',
            
            # 방위산업 (국방 정책)
            'ITA': '항공우주/방위 ETF',
            'PPA': '항공우주/방위 ETF',
            
            # 무역/관세 관련
            'EWJ': '일본 ETF',
            'FXI': '중국 ETF',
            'EWG': '독일 ETF',
            'EWC': '캐나다 ETF',
            
            # 금리/통화 관련
            'TLT': '장기 국채 ETF',
            'UUP': '달러 강세 ETF',
            'GLD': '금 ETF',
            
            # 소비재 (경제정책)
            'XLY': '소비재 ETF',
            'XLP': '필수소비재 ETF',
            'XRT': '소매업 ETF',
            
            # === 한국 ETF ===
            # 한국 주요 지수
            '069500.KS': 'KODEX 200 ETF',
            '102110.KS': 'TIGER 200 ETF',
            '226490.KS': 'KODEX 코스닥150 ETF',
            '229200.KS': 'KODEX 코스닥150선물인버스',
            
        }

    def reset_etf_table(self):
        """etf_prices 테이블만 삭제하고 다시 생성"""
        
        conn = sqlite3.connect("taco_trading.db")
        cursor = conn.cursor()
        
        try:
            logger.info("🗑️  기존 etf_prices 테이블 삭제 중...")
            cursor.execute("DROP TABLE IF EXISTS etf_prices")
            conn.commit()
            logger.info("✅ etf_prices 테이블 삭제 완료")
            
            logger.info("🔄 새로운 etf_prices 테이블 생성 중...")
            ETFPrice.__table__.create(engine, checkfirst=True)
            logger.info("✅ 새로운 etf_prices 테이블 생성 완료")
            
            # 생성된 테이블 구조 확인
            cursor.execute("PRAGMA table_info(etf_prices)")
            columns_info = cursor.fetchall()
            
            logger.info("📋 새로 생성된 etf_prices 테이블 구조:")
            for col in columns_info:
                logger.info(f"  - {col[1]} ({col[2]})")
                
        except Exception as e:
            logger.error(f"❌ 테이블 리셋 중 오류 발생: {str(e)}")
            
        finally:
            conn.close()

    def check_table_structure(self):
        """etf_prices 테이블 구조 확인"""
        
        conn = sqlite3.connect("taco_trading.db")
        cursor = conn.cursor()
        
        try:
            cursor.execute("PRAGMA table_info(etf_prices)")
            columns = cursor.fetchall()
            
            logger.info("현재 etf_prices 테이블 구조:")
            for col in columns:
                logger.info(f"  - {col[1]} ({col[2]})")
                
            # description 컬럼이 있는지 확인
            column_names = [col[1] for col in columns]
            if 'description' in column_names:
                logger.info("✅ description 컬럼이 존재합니다.")
                return True
            else:
                logger.warning("❌ description 컬럼이 없습니다. --reset을 실행하세요.")
                return False
                
        except Exception as e:
            logger.error(f"테이블 구조 확인 중 오류: {str(e)}")
            return False
            
        finally:
            conn.close()
        
    def get_etf_data(self, symbol):
        """단일 ETF의 현재 가격 정보 가져오기"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            hist = ticker.history(period="2d")
            
            if hist.empty or len(hist) < 1:
                logger.warning(f"{symbol}: 가격 데이터를 가져올 수 없음")
                return None
                
            current_price = hist['Close'].iloc[-1]
            
            # 변화율 계산 (전일 대비)
            if len(hist) >= 2:
                previous_close = hist['Close'].iloc[-2]
                change_percent = ((current_price - previous_close) / previous_close) * 100
            else:
                previous_close = info.get('previousClose', current_price)
                if previous_close and previous_close != 0:
                    change_percent = ((current_price - previous_close) / previous_close) * 100
                else:
                    change_percent = 0.0
                
            volume = hist['Volume'].iloc[-1] if 'Volume' in hist.columns else 0
            
            return {
                'symbol': symbol,
                'description': self.etf_symbols[symbol],
                'price': float(current_price),
                'change_percent': float(change_percent),
                'volume': int(volume),
                'timestamp': datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"{symbol} 데이터 가져오기 오류: {str(e)}")
            return None
    
    def update_all_etfs(self):
        """모든 ETF 가격 정보 업데이트"""
        logger.info("미국 + 한국 ETF 가격 업데이트 시작...")
        
        # 테이블 구조 먼저 확인
        if not self.check_table_structure():
            logger.error("테이블 구조에 문제가 있습니다. --reset을 먼저 실행하세요.")
            return
        
        # 데이터베이스 세션 생성
        engine_db = create_engine("sqlite:///./taco_trading.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)
        db = SessionLocal()
        
        updated_count = 0
        
        try:
            for symbol, description in self.etf_symbols.items():
                logger.info(f"{symbol} ({description}) 업데이트 중...")
                
                etf_data = self.get_etf_data(symbol)
                if etf_data is None:
                    continue
                
                # 데이터베이스에 저장 (description 포함)
                etf_price = ETFPrice(
                    symbol=etf_data['symbol'],
                    description=etf_data['description'],
                    price=etf_data['price'],
                    change_percent=etf_data['change_percent'],
                    volume=etf_data['volume'],
                    timestamp=etf_data['timestamp']
                )
                
                db.add(etf_price)
                updated_count += 1
                
                # 한국/미국 구분 표시
                market_flag = "🇰🇷" if ".KS" in symbol else "🇺🇸"
                change_indicator = "📈" if etf_data['change_percent'] > 0 else "📉" if etf_data['change_percent'] < 0 else "➡️"
                
                # 한국 ETF는 원화로, 미국 ETF는 달러로 표시
                if ".KS" in symbol:
                    logger.info(f"{market_flag} {symbol}: ₩{etf_data['price']:,.0f} ({etf_data['change_percent']:+.2f}%) {change_indicator}")
                else:
                    logger.info(f"{market_flag} {symbol}: ${etf_data['price']:.2f} ({etf_data['change_percent']:+.2f}%) {change_indicator}")
            
            db.commit()
            logger.info(f"ETF 가격 업데이트 완료: {updated_count}개 종목")
            
        except Exception as e:
            logger.error(f"데이터베이스 업데이트 오류: {str(e)}")
            db.rollback()
            
        finally:
            db.close()
    
    def get_latest_prices(self):
        """최신 ETF 가격 조회"""
        engine_db = create_engine("sqlite:///./taco_trading.db")
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_db)
        db = SessionLocal()
        
        try:
            latest_prices = {}
            for symbol in self.etf_symbols.keys():
                latest = db.query(ETFPrice).filter_by(symbol=symbol).order_by(ETFPrice.timestamp.desc()).first()
                if latest:
                    latest_prices[symbol] = {
                        'description': latest.description,
                        'price': latest.price,
                        'change_percent': latest.change_percent,
                        'volume': latest.volume,
                        'timestamp': latest.timestamp
                    }
            
            return latest_prices
            
        finally:
            db.close()

def display_current_prices():
    """현재 ETF 가격 출력"""
    updater = ETFPriceUpdater()
    prices = updater.get_latest_prices()
    
    print("\n🌮 === TACO Trading 글로벌 ETF 현재 가격 === 🌮")
    print("\n🇺🇸 === 미국 ETF ===")
    print(f"{'Symbol':<8} {'Description':<30} {'Price':<12} {'Change %':<10}")
    print("-" * 70)
    
    for symbol, data in prices.items():
        if not ".KS" in symbol:  # 미국 ETF
            change_indicator = "📈" if data['change_percent'] > 0 else "📉" if data['change_percent'] < 0 else "➡️"
            change_color = "+" if data['change_percent'] >= 0 else ""
            print(f"{symbol:<8} {data['description'][:29]:<30} ${data['price']:<11.2f} {change_color}{data['change_percent']:<9.2f}% {change_indicator}")
    
    print(f"\n🇰🇷 === 한국 ETF ===")
    print(f"{'Symbol':<12} {'Description':<30} {'Price':<12} {'Change %':<10}")
    print("-" * 74)
    
    for symbol, data in prices.items():
        if ".KS" in symbol:  # 한국 ETF
            change_indicator = "📈" if data['change_percent'] > 0 else "📉" if data['change_percent'] < 0 else "➡️"
            change_color = "+" if data['change_percent'] >= 0 else ""
            print(f"{symbol:<12} {data['description'][:29]:<30} ₩{data['price']:<11,.0f} {change_color}{data['change_percent']:<9.2f}% {change_indicator}")

def update_etf_prices():
    """ETF 가격 업데이트 (스케줄러용)"""
    updater = ETFPriceUpdater()
    updater.update_all_etfs()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='글로벌 ETF 가격 업데이트')
    parser.add_argument('--reset', action='store_true', help='ETF 테이블 리셋 (기존 데이터 삭제)')
    parser.add_argument('--check', action='store_true', help='테이블 구조 확인')
    parser.add_argument('--update', action='store_true', help='ETF 가격 업데이트')
    parser.add_argument('--show', action='store_true', help='현재 가격 조회')
    
    args = parser.parse_args()
    
    updater = ETFPriceUpdater()
    
    if args.reset:
        updater.reset_etf_table()
    elif args.check:
        updater.check_table_structure()
    elif args.update:
        updater.update_all_etfs()
    elif args.show:
        display_current_prices()
    else:
        # 기본 동작: 업데이트 후 조회
        updater.update_all_etfs()
        display_current_prices()