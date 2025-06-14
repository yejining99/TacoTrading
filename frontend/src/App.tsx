import React, { useState, useEffect } from 'react';
import axios from 'axios';

interface TACOSignal {
  id: number;
  signal_type: string;
  confidence: number;
  statement: {
    original: string;
    korean: string;
    keywords: string[];
    posted_at: string;
  };
  affected_etfs: any[];
  created_at: string;
}

interface TrumpStatement {
  id: number;
  original_text: string;
  korean_translation: string;
  keywords: string[];
  taco_probability: number;
  time_ago: string;
}

interface ETFPrice {
  symbol: string;
  price: number;
  change_percent: number;
  volume: number;
  description?: string;
}

interface PerformanceData {
  total_return_30d: number;
  win_rate: number;
  total_profit: number;
  total_signals: number;
  successful_signals: number;
  average_holding_days: number;
}

function App() {
  const [signals, setSignals] = useState<TACOSignal[]>([]);
  const [statements, setStatements] = useState<TrumpStatement[]>([]);
  const [etfPrices, setETFPrices] = useState<ETFPrice[]>([]);
  const [performance, setPerformance] = useState<PerformanceData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  useEffect(() => {
    fetchData();
    
    // 30초마다 데이터 새로고침
    const interval = setInterval(() => {
      console.log('🔄 자동 데이터 새로고침...');
      fetchData();
    }, 30000);
    
    return () => clearInterval(interval);
  }, []);

  const fetchData = async () => {
    try {
      setError(null);
      // 개발 환경에서는 백엔드 서버 직접 호출
      const baseURL = 'http://localhost:8000';
      
      console.log('🌮 백엔드 서버 연결 시도...', baseURL);
      console.log('현재 시간:', new Date().toLocaleTimeString());
      
      // 각 API를 개별적으로 호출하여 어느 것이 실패하는지 확인
      console.log('1️⃣ 신호 데이터 요청 중...');
      const signalsRes = await axios.get(`${baseURL}/api/latest-signals`);
      console.log('✅ 신호 데이터 성공:', signalsRes.data);
      
      console.log('2️⃣ 발언 데이터 요청 중...');
      const statementsRes = await axios.get(`${baseURL}/api/trump-feed`);
      console.log('✅ 발언 데이터 성공:', statementsRes.data);
      
      console.log('3️⃣ ETF 데이터 요청 중...');
      const pricesRes = await axios.get(`${baseURL}/api/etf-prices`);
      console.log('✅ ETF 데이터 성공:', pricesRes.data);
      
      console.log('4️⃣ 성과 데이터 요청 중...');
      const performanceRes = await axios.get(`${baseURL}/api/performance`);
      console.log('✅ 성과 데이터 성공:', performanceRes.data);

      console.log('🎉 모든 데이터 로드 완료!');
      console.log('신호 수:', signalsRes.data.signals?.length || 0);
      console.log('발언 수:', statementsRes.data.statements?.length || 0);
      console.log('ETF 수:', pricesRes.data.etf_prices?.length || 0);

      setSignals(signalsRes.data.signals || []);
      setStatements(statementsRes.data.statements || []);
      setETFPrices(pricesRes.data.etf_prices || []);
      setPerformance(performanceRes.data);
      setLastUpdate(new Date());
      setLoading(false);
      
      console.log('📊 State 업데이트 완료');
    } catch (error: any) {
      console.error('❌ 데이터 로드 오류:', error);
      console.error('에러 타입:', typeof error);
      console.error('에러 이름:', error.name);
      console.error('에러 메시지:', error.message);
      console.error('에러 스택:', error.stack);
      console.error('응답 상태:', error.response?.status);
      console.error('응답 데이터:', error.response?.data);
      console.error('에러 코드:', error.code);
      
      const errorMessage = error.response?.status === 404 
        ? '백엔드 API를 찾을 수 없습니다. 서버가 실행 중인지 확인하세요.'
        : error.code === 'ECONNREFUSED' || error.message.includes('ECONNREFUSED')
        ? '백엔드 서버 연결 실패. localhost:8000에서 서버를 실행하세요.'
        : error.message.includes('CORS')
        ? 'CORS 오류입니다. 백엔드 서버를 다시 시작해보세요.'
        : `데이터를 불러오는 중 오류가 발생했습니다: ${error.message}`;
      
      setError(errorMessage);
      setLoading(false);
      
      // 오류 발생 시 빈 배열로 설정
      setSignals([]);
      setStatements([]);
      setETFPrices([]);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#0A0A0A', color: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '2rem', marginBottom: '10px' }}>🌮</div>
          <div>TACO 데이터 로딩 중...</div>
          <div style={{ fontSize: '0.8rem', color: '#98989D', marginTop: '10px' }}>
            백엔드 서버 연결 중...
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '100vh', backgroundColor: '#0A0A0A', color: '#fff' }}>
        <div style={{ textAlign: 'center', maxWidth: '500px', padding: '20px' }}>
          <div style={{ fontSize: '2rem', marginBottom: '20px' }}>❌</div>
          <div style={{ fontSize: '1.2rem', marginBottom: '15px', color: '#FF3B30' }}>
            연결 오류
          </div>
          <div style={{ marginBottom: '20px', color: '#98989D' }}>
            {error}
          </div>
          <div style={{ fontSize: '0.9rem', color: '#636366', lineHeight: '1.5' }}>
            <div>해결 방법:</div>
            <div>1. 백엔드 서버 실행: <code style={{ background: '#1C1C1E', padding: '2px 6px', borderRadius: '4px' }}>cd backend && python -m app.main</code></div>
            <div>2. 서버 주소 확인: <code style={{ background: '#1C1C1E', padding: '2px 6px', borderRadius: '4px' }}>http://localhost:8000</code></div>
          </div>
          <button 
            onClick={fetchData}
            style={{
              marginTop: '20px',
              padding: '10px 20px',
              background: '#007AFF',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            다시 시도
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '20px', backgroundColor: '#0A0A0A', color: '#fff', minHeight: '100vh' }}>
      <h1 style={{ textAlign: 'center', marginBottom: '30px' }}>
        🌮 TACO(Trump Always Chickens Out) Trading
      </h1>
      


      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '20px' }}>
        {/* 트럼프 피드 */}
        <div style={{ background: '#1C1C1E', padding: '20px', borderRadius: '12px' }}>
          <h3>🎙️ Trump Intelligence Feed</h3>
          {statements.map(stmt => (
            <div key={stmt.id} style={{
              background: '#0A0A0A',
              padding: '15px',
              margin: '10px 0',
              borderRadius: '8px',
              border: '1px solid #38383A'
            }}>
              {/* 한국어 번역 */}
              <div style={{ marginBottom: '6px' }}>{stmt.korean_translation}</div>
              {/* 원문 영어 */}
              <div style={{ 
                marginBottom: '10px', 
                color: '#98989D', 
                fontSize: '0.85rem', 
                fontStyle: 'italic' 
              }}>
                "{stmt.original_text}"
              </div>
              <div style={{ 
                background: 'rgba(255, 255, 255, 0.05)',
                padding: '10px',
                borderRadius: '6px',
                fontSize: '0.8rem'
              }}>
                <div>🔍 키워드: {stmt.keywords.join(', ')}</div>
                <div>🌮 TACO 확률: {typeof stmt.taco_probability === 'number' ?
                  (stmt.taco_probability <= 1 ? (stmt.taco_probability * 100).toFixed(0) : stmt.taco_probability.toFixed(0))
                  : stmt.taco_probability}%</div>
              </div>
              <div style={{ 
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                marginTop: '10px',
                fontSize: '0.8rem',
                color: '#636366'
              }}>
                <span>{stmt.time_ago} • Truth Social</span>
                <div>
                  <span style={{ 
                    background: '#007AFF',
                    color: 'white',
                    padding: '2px 6px',
                    borderRadius: '6px',
                    marginRight: '5px'
                  }}>🤖 AI 번역</span>
                  {(() => {
                    const prob = typeof stmt.taco_probability === 'number'
                      ? (stmt.taco_probability <= 1 ? stmt.taco_probability * 100 : stmt.taco_probability)
                      : 0;
                    return prob >= 80 ? (
                      <span style={{ 
                        background: '#FF3B30',
                        color: 'white',
                        padding: '2px 6px',
                        borderRadius: '6px'
                      }}>높은 영향</span>
                    ) : null;
                  })()}
                </div>
              </div>
            </div>
          ))}
        </div>

        {/* ETF 가격 */}
        <div style={{ background: '#1C1C1E', padding: '20px', borderRadius: '12px' }}>
          <h3>📊 Market Pulse</h3>
          {etfPrices
            .slice() // 원본 배열 보호
            .sort((a, b) => b.change_percent - a.change_percent)
            .map(etf => (
              <div key={etf.symbol} style={{
                display: 'flex',
                flexDirection: 'column',
                padding: '10px',
                margin: '5px 0',
                background: '#0A0A0A',
                borderRadius: '6px'
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <span style={{ fontWeight: 'bold', fontFamily: 'monospace' }}>{etf.symbol}</span>
                  <span style={{ 
                    color: etf.change_percent >= 0 ? '#00D084' : '#FF3B30',
                    fontWeight: 'bold',
                    fontFamily: 'monospace'
                  }}>
                    {etf.change_percent >= 0 ? '+' : ''}{etf.change_percent.toFixed(1)}%
                  </span>
                </div>
                {etf.description && (
                  <div style={{ color: '#98989D', fontSize: '0.85rem', marginTop: '4px' }}>
                    {etf.description}
                  </div>
                )}
              </div>
            ))}
        </div>
      </div>

      <div style={{ textAlign: 'center', marginTop: '30px', color: '#636366' }}>
        <div style={{ marginBottom: '10px' }}>
          🌮 TACO Trading - 
          <span style={{ color: '#00D084', marginLeft: '5px' }}>
            ✅ API 연결 성공!
          </span>
        </div>
        <div style={{ fontSize: '0.8rem' }}>
          신호: {signals.length}개 | 발언: {statements.length}개 | ETF: {etfPrices.length}개
        </div>
        <div style={{ fontSize: '0.7rem', marginTop: '5px' }}>
          마지막 업데이트: {lastUpdate.toLocaleTimeString('ko-KR')}
          <span style={{ color: '#00D084', marginLeft: '10px' }}>🔄 30초마다 자동 새로고침</span>
        </div>
      </div>
    </div>
  );
}

export default App;