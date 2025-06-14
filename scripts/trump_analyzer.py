import os
import openai
from datetime import datetime, timedelta
import requests
import json
import pandas as pd
from typing import List, Dict
import time

class TrumpAnalyzer:
    def __init__(self, openai_api_key: str):
        """트럼프 분석기 초기화"""
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key
        
    def collect_news(self, days: int = 7) -> List[Dict]:
        """트럼프 관련 뉴스 수집"""
        # News API를 사용하여 뉴스 수집
        # 실제 사용시 API 키 필요
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
            print(f"뉴스 수집 중 오류 발생: {e}")
            return []

    def analyze_with_gpt(self, text: str) -> Dict:
        """OpenAI API를 사용하여 텍스트 분석"""
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a political analyst specializing in analyzing Trump-related news. Analyze the following text and provide insights about its sentiment, key points, and potential market impact."},
                    {"role": "user", "content": text}
                ],
                temperature=0.7,
                max_tokens=500
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"GPT 분석 중 오류 발생: {e}")
            return None

    def process_news_batch(self, news_articles: List[Dict], batch_size: int = 5) -> List[Dict]:
        """뉴스 기사를 배치로 처리"""
        results = []
        
        for i in range(0, len(news_articles), batch_size):
            batch = news_articles[i:i + batch_size]
            for article in batch:
                if article.get('description'):
                    analysis = self.analyze_with_gpt(article['description'])
                    if analysis:
                        results.append({
                            'title': article.get('title', ''),
                            'description': article.get('description', ''),
                            'analysis': analysis,
                            'published_at': article.get('publishedAt', '')
                        })
            time.sleep(1)  # API 호출 제한을 위한 대기
            
        return results

    def save_analysis(self, results: List[Dict], filename: str = 'trump_analysis.json'):
        """분석 결과 저장"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)

    def generate_summary(self, results: List[Dict]) -> str:
        """전체 분석 결과 요약"""
        combined_text = "\n".join([f"Title: {r['title']}\nAnalysis: {r['analysis']}" for r in results])
        
        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a political analyst. Provide a comprehensive summary of the following analyses about Trump-related news."},
                    {"role": "user", "content": combined_text}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            return response.choices[0].message.content
        except Exception as e:
            print(f"요약 생성 중 오류 발생: {e}")
            return None

def main():
    # OpenAI API 키 설정
    openai_api_key = os.getenv('OPENAI_API_KEY')
    if not openai_api_key:
        print("OPENAI_API_KEY 환경 변수를 설정해주세요.")
        return

    analyzer = TrumpAnalyzer(openai_api_key)
    
    # 뉴스 수집
    print("뉴스 수집 중...")
    news_articles = analyzer.collect_news()
    
    if not news_articles:
        print("수집된 뉴스가 없습니다.")
        return
    
    # 뉴스 분석
    print("뉴스 분석 중...")
    analysis_results = analyzer.process_news_batch(news_articles)
    
    # 결과 저장
    analyzer.save_analysis(analysis_results)
    
    # 전체 요약 생성
    print("전체 요약 생성 중...")
    summary = analyzer.generate_summary(analysis_results)
    
    if summary:
        print("\n=== 분석 요약 ===")
        print(summary)
        print("\n상세 분석 결과는 trump_analysis.json 파일에 저장되었습니다.")

if __name__ == "__main__":
    main() 