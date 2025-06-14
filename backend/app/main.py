from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from .database import get_db, init_db
from .model import TrumpStatement, TACOSignal, ETFPrice
import random
from datetime import datetime, timedelta
import json

app = FastAPI(title="🌮 TACO Trading API", version="1.0.0")

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """서버 시작시 데이터베이스 초기화 및 샘플 데이터 생성"""
    init_db()
    await create_sample_data()

async def create_sample_data():
    """데모용 샘플 데이터 생성"""
    db = next(get_db())
    
    # 기존 데이터가 있으면 스킵
    if db.query(TrumpStatement).count() > 0:
        db.close()
        return
    # 기존 데이터가 없음을 표시
    print("✅ 기존 데이터가 없습니다. 샘플 데이터를 생성합니다.")
    # 샘플 트럼프 발언
    sample_statements = [
        {
            "original": "The European Union must pay their fair share! We are giving them until July 9th to make a deal. Otherwise, 50% tariffs will be imposed!",
            "korean": "유럽연합은 공정한 몫을 지불해야 한다! 우리는 그들에게 7월 9일까지 합의를 이룰 시간을 주고 있다. 그렇지 않으면 50% 관세가 부과될 것이다!",
            "keywords": ["유럽연합", "관세", "7월 9일"],
            "taco_probability": 92.0,
            "signal_type": "BUY"
        },
        {
            "original": "China has been very fair in our negotiations. We are making tremendous progress!",
            "korean": "중국은 우리의 협상에서 매우 협조적이었다. 우리는 엄청난 진전을 이루고 있다!",
            "keywords": ["중국", "협상", "진전"],
            "taco_probability": 84.0,
            "signal_type": "BUY"
        },
        {
            "original": "Europe trade negotiations ongoing. Mixed signals from Brussels.",
            "korean": "유럽 무역 협상이 진행 중이다. 브뤼셀에서 엇갈린 신호가 오고 있다.",
            "keywords": ["유럽", "무역협상", "브뤼셀"],
            "taco_probability": 67.0,
            "signal_type": "WATCH"
        }
    ]
    
    # 샘플 데이터 삽입
    for i, stmt_data in enumerate(sample_statements):
        # 트럼프 발언 생성
        statement = TrumpStatement(
            original_text=stmt_data["original"],
            korean_translation=stmt_data["korean"],
            keywords=stmt_data["keywords"],# [k.strip() for k in stmt_data["keywords"].split(',')]
            taco_probability=stmt_data["taco_probability"], 
            is_analyzed=True,
            posted_at=datetime.now() - timedelta(minutes=i*5)
        )
        db.add(statement)
        db.flush()
        
        # TACO 신호 생성
        signal = TACOSignal(
            statement_id=statement.id,
            signal_type=stmt_data["signal_type"],
            confidence=stmt_data["taco_probability"],
            affected_etfs=[
                {"symbol": "XLK", "direction": "up", "impact": 0.8},
                {"symbol": "VGK", "direction": "up", "impact": 0.9}
            ]
        )
        db.add(signal)
    
    # 샘플 ETF 가격
    etf_symbols = ["XLK", "VGK", "FXI", "XLY", "SPY", "XLI"]
    for symbol in etf_symbols:
        price = ETFPrice(
            symbol=symbol,
            price=round(random.uniform(50, 200), 2),
            change_percent=round(random.uniform(-5, 5), 2),
            volume=random.randint(1000000, 10000000)
        )
        db.add(price)
    
    db.commit()
    db.close()

@app.get("/")
async def root():
    return {"message": "🌮 TACO Trading API is running!", "status": "healthy"}

@app.get("/api/latest-signals")
async def get_latest_signals(limit: int = 10, db: Session = Depends(get_db)):
    """최신 TACO 신호 조회"""
    signals = db.query(TACOSignal).filter(
        TACOSignal.is_active == True
    ).order_by(TACOSignal.created_at.desc()).limit(limit).all()
    
    result = []
    for signal in signals:
        statement = db.query(TrumpStatement).filter(
            TrumpStatement.id == signal.statement_id
        ).first()
        
        result.append({
            "id": signal.id,
            "signal_type": signal.signal_type,
            "confidence": signal.confidence,
            "statement": {
                "original": statement.original_text,
                "korean": statement.korean_translation,
                "keywords": [k.strip() for k in statement.keywords.split(',')], # statement.keywords,
                "posted_at": statement.posted_at.isoformat()
            },
            "affected_etfs": signal.affected_etfs,
            "created_at": signal.created_at.isoformat(),
            "entry_timing": signal.entry_timing
        })
    
    return {"signals": result}

@app.get("/api/trump-feed")
async def get_trump_feed(limit: int = 20, db: Session = Depends(get_db)):
    """트럼프 최신 발언 피드"""
    statements = db.query(TrumpStatement).filter(
        TrumpStatement.is_analyzed == True
    ).order_by(TrumpStatement.posted_at.desc()).limit(limit).all()
    
    result = []
    for stmt in statements:
        # 시간 차이 계산
        time_diff = datetime.now() - stmt.posted_at
        if time_diff.days > 0:
            time_ago = f"{time_diff.days}일 전"
        elif time_diff.seconds > 3600:
            hours = time_diff.seconds // 3600
            time_ago = f"{hours}시간 전"
        elif time_diff.seconds > 60:
            minutes = time_diff.seconds // 60
            time_ago = f"{minutes}분 전"
        else:
            time_ago = "방금 전"
        
        result.append({
            "id": stmt.id,
            "original_text": stmt.original_text,
            "korean_translation": stmt.korean_translation,
            "keywords": [k.strip() for k in stmt.keywords.split(',')], # stmt.keywords,
            "taco_probability": stmt.taco_probability,
            "source": stmt.source,
            "posted_at": stmt.posted_at.isoformat(),
            "time_ago": time_ago
        })
    
    return {"statements": result}

@app.get("/api/etf-prices")
async def get_etf_prices(symbols: str = None, db: Session = Depends(get_db)):
    """ETF 가격 데이터 조회"""
    query = db.query(ETFPrice)
    
    if symbols:
        symbol_list = [s.strip().upper() for s in symbols.split(',')]
        query = query.filter(ETFPrice.symbol.in_(symbol_list))
    
    prices = query.order_by(ETFPrice.timestamp.desc()).all()
    
    result = []
    for price in prices:
        result.append({
            "symbol": price.symbol,
            "description": price.description,
            "price": price.price,
            "change_percent": price.change_percent,
            "volume": price.volume,
            "timestamp": price.timestamp.isoformat()
        })
    
    return {"etf_prices": result}

@app.get("/api/performance")
async def get_performance(db: Session = Depends(get_db)):
    """TACO 성과 데이터"""
    total_signals = db.query(TACOSignal).count()
    successful_signals = int(total_signals * 0.78)  # 78% 성공률
    
    return {
        "total_return_30d": 127.5,
        "win_rate": 78.0,
        "total_profit": 12450.0,
        "total_signals": total_signals,
        "successful_signals": successful_signals,
        "average_holding_days": 3.2
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)