import os
import openai
from datetime import datetime, timedelta
import requests
import json
import logging
from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from .database import get_db
from .model import TrumpStatement, TACOSignal
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TrumpAnalyzer:
    def __init__(self, openai_api_key: str):
        """트럼프 분석기 초기화"""
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        
    def collect_news(self, days: int = 7) -> List[Dict]:
        """트럼프 관련 뉴스 수집"""
        news_url = "https://newsapi.org/v2/everything"
        params = {
            'q': 'Trump',
            'from': (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d'),
            'sortBy': 'publishedAt',
            'language': 'en'
        }
        
        try:
            response = requests.get(news_url, params=params)
            news_data = response.json()
            return news_data.get('articles', [])
        except Exception as e:
            logger.error(f"뉴스 수집 중 오류 발생: {e}")
            return []

    def translate_to_korean(self, text: str) -> Optional[str]:
        """영문 텍스트를 한글로 번역"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """당신은 전문 번역가입니다. 
                    다음 영문 텍스트를 자연스러운 한국어로 번역해주세요.
                    번역 시 다음 사항을 고려해주세요:
                    1. 자연스러운 한국어 표현 사용
                    2. 정치적 맥락 유지
                    3. 전문 용어의 정확한 번역
                    4. 문맥에 맞는 어조 유지"""},
                    {"role": "user", "content": text}
                ],
                temperature=0.3,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"번역 중 오류 발생: {e}")
            return None

    def analyze_with_gpt(self, text: str) -> Dict:
        """OpenAI API를 사용하여 텍스트 분석"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": """당신은 트럼프 관련 뉴스를 분석하는 정치/경제 전문가입니다.
                    다음 텍스트를 분석하여 JSON 형식으로 응답해주세요.
                    
                    분석해야 할 항목:
                    1. key_points: 주요 포인트 목록 (한국어로)
                    2. sentiment_score: 감성 점수 (-1 ~ 1)
                    3. trade_relevance: 무역 관련성 (0 ~ 100)
                    4. taco_probability: TACO 확률 (0 ~ 100)
                    5. signal_type: 매매 신호 ("BUY", "SELL", "WATCH" 중 하나)
                    6. affected_etfs: 영향받는 ETF 목록
                    
                    분석 시 고려사항:
                    - 무역 정책 관련성
                    - 시장 영향도
                    - 정치적 맥락
                    - 경제적 파급효과
                    
                    응답 형식:
                    {
                        "key_points": ["주요 포인트1", "주요 포인트2"],
                        "sentiment_score": 0.8,
                        "trade_relevance": 85,
                        "taco_probability": 90,
                        "signal_type": "BUY",
                        "affected_etfs": [
                            {
                                "symbol": "XLK",
                                "direction": "up",
                                "impact": 0.8
                            }
                        ]
                    }"""},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"GPT 분석 중 오류 발생: {e}")
            return None

    def save_to_db(self, news_articles: List[Dict], db: Session):
        """분석 결과를 데이터베이스에 저장"""
        saved_count = 0
        
        try:
            for article in news_articles:
                # 중복 체크
                existing = db.query(TrumpStatement).filter_by(
                    original_text=article['description']
                ).first()
                
                if not existing:
                    # GPT 분석 수행
                    analysis = self.analyze_with_gpt(article['description'])
                    if analysis:
                        # 한글 번역
                        korean_translation = self.translate_to_korean(article['description'])
                        
                        # 트럼프 발언 저장
                        statement = TrumpStatement(
                            original_text=article['description'],
                            korean_translation=korean_translation,
                            source=article.get('source', {}).get('name', 'Unknown'),
                            posted_at=datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')),
                            keywords=','.join(analysis.get('key_points', [])),
                            sentiment_score=analysis.get('sentiment_score', 0),
                            trade_relevance=analysis.get('trade_relevance', 0),
                            taco_probability=analysis.get('taco_probability', 0),
                            is_analyzed=True
                        )
                        db.add(statement)
                        db.flush()
                        
                        # TACO 신호 저장
                        signal = TACOSignal(
                            statement_id=statement.id,
                            signal_type=analysis.get('signal_type', 'WATCH'),
                            confidence=analysis.get('taco_probability', 0),
                            affected_etfs=analysis.get('affected_etfs', []),
                            entry_timing="immediate",
                            expected_duration=24,
                            is_active=True
                        )
                        db.add(signal)
                        saved_count += 1
                        
                        # API 호출 제한을 위한 대기
                        time.sleep(1)
            
            db.commit()
            logger.info(f"{saved_count}개의 새로운 분석 결과가 저장되었습니다.")
            
        except Exception as e:
            logger.error(f"데이터베이스 저장 중 오류: {str(e)}")
            db.rollback()
            raise

def main():
    # OpenAI API 키 설정
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        logger.error("OPENAI_API_KEY 환경 변수를 설정해주세요.")
        return

    analyzer = TrumpAnalyzer(openai_api_key)
    db = next(get_db())
    
    try:
        # 뉴스 수집
        logger.info("뉴스 수집 중...")
        news_articles = analyzer.collect_news()
        
        if not news_articles:
            logger.warning("수집된 뉴스가 없습니다.")
            return
        
        # 분석 및 저장
        logger.info("뉴스 분석 및 저장 중...")
        analyzer.save_to_db(news_articles, db)
        
    except Exception as e:
        logger.error(f"실행 중 오류 발생: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()