# 🌮 TACO Trading

트럼프의 발언과 글로벌 ETF 시장을 분석하는 AI 기반 트레이딩 대시보드입니다.

## 📋 프로젝트 개요

TACO Trading은 트럼프의 발언을 실시간으로 분석하고, 이를 기반으로 글로벌 ETF 시장의 트레이딩 시그널을 제공하는 웹 애플리케이션입니다. OpenAI의 GPT 모델을 활용하여 트럼프의 발언을 분석하고, 이를 바탕으로 투자 기회를 포착합니다.

## 🚀 주요 기능

- **실시간 트럼프 발언 분석**
  - SNS 및 뉴스 크롤링
  - GPT 기반 발언 분석
  - 한글 번역 및 키워드 추출

- **ETF 트레이딩 시그널**
  - 글로벌 ETF 가격 실시간 모니터링
  - AI 기반 매수/매도 시그널 생성
  - 30일 수익률 및 승률 분석

- **대시보드 시각화**
  - 실시간 트레이딩 시그널 표시
  - 수익률 및 성과 지표 차트
  - 트럼프 발언 타임라인

## 🚀 실행 방법

### 백엔드 서버 실행
```bash
cd backend
python run.py
```

### 프론트엔드 개발 서버 실행
```bash
cd frontend
npm start
```

### 일일 업데이트 스크립트 실행
```bash
cd scripts
python daily_update.py
```

## 📊 데이터베이스 구조

- `TrumpStatement`: 트럼프 발언 데이터
- `TACOSignal`: 트레이딩 시그널 데이터
- `ETFPrice`: ETF 가격 데이터

## 🔄 자동화된 업데이트

Windows 환경에서는 `scripts/daily_update.bat`를 사용하여 자동 업데이트를 설정할 수 있습니다. 이 스크립트는 다음 작업들을 순차적으로 실행합니다:

1. 트럼프 SNS 크롤링
2. LLM 기반 발언 분석
3. ETF 데이터 업데이트


## 🛠 기술 스택

### 백엔드
- FastAPI 0.104.1
- PostgreSQL
- OpenAI API
- Tweepy (트위터 API)

### 프론트엔드
- React 18.2.0

## 사용한 AI 기술
- Claude + MCP
