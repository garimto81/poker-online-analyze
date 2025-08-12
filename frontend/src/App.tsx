import React, { useState, useEffect, useRef, useCallback } from 'react';
import axios from 'axios';
import firebaseService from './services/firebaseService';
import TrendChart from './components/TrendChart';
import MarketShareStackedChart from './components/MarketShareStackedChart';
import './App.css';

interface Site {
  site_name: string;
  category: string;
  players_online: number;
  cash_players: number;
  peak_24h: number;
  seven_day_avg: number;
  last_updated?: string;
  rank?: number;
  players_share?: number;
  cash_share?: number;
}

interface AllSitesData {
  total_sites: number;
  data: {
    [key: string]: {
      current_stats: Site;
      daily_data: Array<{
        date: string;
        players_online: number;
        cash_players: number;
        peak_24h: number;
        seven_day_avg: number;
      }>;
    };
  };
  days: number;
}

type SortField = 'rank' | 'site_name' | 'category' | 'players_online' | 'cash_players' | 'peak_24h' | 'seven_day_avg' | 'players_share' | 'cash_share';
type SortDirection = 'asc' | 'desc';

function App() {
  const [sites, setSites] = useState<Site[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [errorType, setErrorType] = useState<'network' | 'ratelimit' | 'server' | null>(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [allSitesData, setAllSitesData] = useState<AllSitesData | null>(null);
  const [activeTab, setActiveTab] = useState<'table' | 'charts'>('table');
  const [sortField, setSortField] = useState<SortField>('players_online');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
  const [fallbackData, setFallbackData] = useState<Site[] | null>(null);
  const [isDataFresh, setIsDataFresh] = useState(false); // 데이터 신선도 상태
  const [lastFetchAttempt, setLastFetchAttempt] = useState<number>(0); // 마지막 fetch 시도 시간

  // API URL 환경 변수 설정 with fallbacks
  const API_BASE_URL = process.env.REACT_APP_API_URL || 
    (process.env.NODE_ENV === 'production' 
      ? 'https://poker-analyzer-api.vercel.app' 
      : 'http://localhost:4001');

  console.log('Environment variables:');
  console.log('- NODE_ENV:', process.env.NODE_ENV);
  console.log('- API_BASE_URL:', API_BASE_URL);
  console.log('- REACT_APP_API_URL:', process.env.REACT_APP_API_URL);
  console.log('- REACT_APP_FIREBASE_PROJECT_ID:', process.env.REACT_APP_FIREBASE_PROJECT_ID);
  console.log('- PUBLIC_URL:', process.env.PUBLIC_URL);

  // 디바운스를 위한 타이머 참조
  const fetchTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  useEffect(() => {
    // 앱 시작 시 로컬 저장소에서 캐시된 데이터 로드
    const initializeData = async () => {
      const hasCachedData = loadCachedData();
      if (!hasCachedData) {
        // 캐시된 데이터가 없을 때만 새로 fetch
        await fetchCurrentRanking();
      }
      await fetchAllSitesStats();
    };
    initializeData();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  // 컴포넌트 언마운트 시 타이머 정리
  useEffect(() => {
    return () => {
      if (fetchTimeoutRef.current) {
        clearTimeout(fetchTimeoutRef.current);
      }
    };
  }, []);

  // 로컬 저장소에서 캐시된 데이터 로드
  const loadCachedData = (): boolean => {
    try {
      const cachedSites = localStorage.getItem('poker-sites-cache');
      const cachedStats = localStorage.getItem('poker-stats-cache');
      const cacheTimestamp = localStorage.getItem('poker-cache-timestamp');
      
      if (cachedSites && cachedStats && cacheTimestamp) {
        const timestamp = parseInt(cacheTimestamp);
        const isExpired = Date.now() - timestamp > 15 * 60 * 1000; // 15분 캐시
        
        if (!isExpired) {
          const sites = JSON.parse(cachedSites);
          const stats = JSON.parse(cachedStats);
          
          setFallbackData(sites);
          setSites(sites);
          setAllSitesData(stats);
          
          if (sites.length > 0 && sites[0].last_updated) {
            setLastUpdate(`${new Date(sites[0].last_updated).toLocaleString()} (캐시됨)`);
          }
          
          console.log('Loaded cached data successfully');
          return true; // 캐시 데이터 로드 성공
        } else {
          // 캐시 만료 시 정리
          localStorage.removeItem('poker-sites-cache');
          localStorage.removeItem('poker-stats-cache');
          localStorage.removeItem('poker-cache-timestamp');
          return false;
        }
      }
      return false;
    } catch (error) {
      console.warn('Failed to load cached data:', error);
      return false;
    }
  };

  // 데이터를 로컬 저장소에 캐시
  const cacheData = (sites: Site[], stats: AllSitesData | null) => {
    try {
      localStorage.setItem('poker-sites-cache', JSON.stringify(sites));
      if (stats) {
        localStorage.setItem('poker-stats-cache', JSON.stringify(stats));
      }
      localStorage.setItem('poker-cache-timestamp', Date.now().toString());
    } catch (error) {
      console.warn('Failed to cache data:', error);
    }
  };

  // 에러 타입 판별
  const getErrorType = (error: any): 'network' | 'ratelimit' | 'server' => {
    const errorMessage = error?.message || error?.toString() || '';
    
    if (errorMessage.includes('429') || errorMessage.includes('Rate limit') || errorMessage.includes('quota')) {
      return 'ratelimit';
    } else if (errorMessage.includes('network') || errorMessage.includes('fetch')) {
      return 'network';
    } else {
      return 'server';
    }
  };

  // 자동 재시도 로직
  const retryWithDelay = async (retryFunction: () => Promise<void>, currentRetryCount: number) => {
    const maxRetries = 3;
    const baseDelay = 2000; // 2초
    
    if (currentRetryCount < maxRetries) {
      const delay = baseDelay * Math.pow(2, currentRetryCount); // 지수 백오프
      
      setIsRetrying(true);
      setRetryCount(currentRetryCount + 1);
      
      console.log(`Retrying in ${delay}ms... (${currentRetryCount + 1}/${maxRetries})`);
      
      setTimeout(async () => {
        try {
          await retryFunction();
          setIsRetrying(false);
          setRetryCount(0);
          setError(null);
          setErrorType(null);
        } catch (err) {
          const newErrorType = getErrorType(err);
          if (newErrorType === 'ratelimit') {
            await retryWithDelay(retryFunction, currentRetryCount + 1);
          } else {
            setIsRetrying(false);
            setError(err instanceof Error ? err.message : 'Unknown error');
            setErrorType(newErrorType);
          }
        }
      }, delay);
    } else {
      setIsRetrying(false);
      setError('최대 재시도 횟수에 도달했습니다. 잠시 후 다시 시도해 주세요.');
      setErrorType('ratelimit');
      
      // 재시도 실패 시 캐시된 데이터 사용
      if (fallbackData && fallbackData.length > 0) {
        setSites(fallbackData);
        setLastUpdate(`${new Date().toLocaleString()} (캐시된 데이터 사용)`);
      }
    }
  };

  // 디바운스된 fetch 함수 (중복 호출 방지)
  const debouncedFetch = (fetchFunction: () => Promise<void>, delay: number = 1000) => {
    if (fetchTimeoutRef.current) {
      clearTimeout(fetchTimeoutRef.current);
    }

    fetchTimeoutRef.current = setTimeout(() => {
      const now = Date.now();
      // 최소 간격 확인 (5초)
      if (now - lastFetchAttempt < 5000) {
        console.log('Too frequent fetch attempts, skipping...');
        return;
      }
      
      setLastFetchAttempt(now);
      fetchFunction();
    }, delay);
  };

  // 데이터 신선도 확인
  const isDataStale = (): boolean => {
    const now = Date.now();
    const cacheTimestamp = localStorage.getItem('poker-cache-timestamp');
    
    if (!cacheTimestamp) return true;
    
    const age = now - parseInt(cacheTimestamp);
    return age > 10 * 60 * 1000; // 10분 이상 오래된 데이터는 stale
  };

  const fetchCurrentRanking = async (force: boolean = false) => {
    // 강제 갱신이 아니고 데이터가 신선하면 스킵
    if (!force && !isDataStale() && sites.length > 0) {
      console.log('Data is fresh, skipping fetch');
      setIsDataFresh(true);
      return;
    }

    const fetchLogic = async () => {
      setLoading(true);
      setError(null);
      setErrorType(null);
      setIsDataFresh(false);
      
      let sitesData: Site[] = [];
      
      // 먼저 API 서버 시도
      try {
        console.log(`Trying API server: ${API_BASE_URL}/api/firebase/current_ranking/`);
        const response = await axios.get(`${API_BASE_URL}/api/firebase/current_ranking/`, {
          timeout: 10000 // 10초 타임아웃
        });
        sitesData = response.data;
        if (response.data.length > 0 && response.data[0].last_updated) {
          setLastUpdate(new Date(response.data[0].last_updated).toLocaleString());
        }
        console.log('Data loaded from API server successfully:', sitesData.length, 'sites');
      } catch (apiError) {
        console.log('API server failed, trying Firebase direct connection...', apiError);
        
        // API 실패시 Firebase 직접 연결 시도
        try {
          const firebaseData = await firebaseService.getCurrentRanking();
          sitesData = firebaseData;
          if (firebaseData.length > 0 && firebaseData[0].last_updated) {
            setLastUpdate(new Date(firebaseData[0].last_updated).toLocaleString());
          }
          console.log('Data loaded from Firebase directly:', sitesData.length, 'sites');
        } catch (firebaseError) {
          console.error('Firebase direct connection also failed:', firebaseError);
          
          // 마지막 방법: 로컬 캐시 또는 fallback 데이터 사용
          if (fallbackData && fallbackData.length > 0) {
            sitesData = fallbackData;
            setLastUpdate(`${new Date().toLocaleString()} (캐시된 데이터 사용)`);
            console.log('Using cached fallback data:', sitesData.length, 'sites');
          } else {
            // 모든 방법이 실패한 경우 데모 데이터 제공
            sitesData = [
              {
                site_name: 'PokerStars',
                category: 'STANDALONE',
                players_online: 8500,
                cash_players: 3200,
                peak_24h: 12000,
                seven_day_avg: 9800,
                rank: 1
              },
              {
                site_name: 'GGPoker',
                category: 'GG_POKER',
                players_online: 7200,
                cash_players: 2800,
                peak_24h: 10500,
                seven_day_avg: 8100,
                rank: 2
              }
            ];
            setLastUpdate(`${new Date().toLocaleString()} (데모 데이터)`);
            console.log('Using demo data as fallback');
          }
        }
      }
      
      // 점유율 계산
      const totalPlayers = sitesData.reduce((sum, site) => sum + site.players_online, 0);
      const totalCashPlayers = sitesData.reduce((sum, site) => sum + site.cash_players, 0);
      
      const sitesWithShare = sitesData.map(site => ({
        ...site,
        players_share: totalPlayers > 0 ? (site.players_online / totalPlayers) * 100 : 0,
        cash_share: totalCashPlayers > 0 ? (site.cash_players / totalCashPlayers) * 100 : 0
      }));
      
      setSites(sitesWithShare);
      setFallbackData(sitesWithShare); // 새로운 데이터를 fallback으로 저장
      setIsDataFresh(true); // 데이터가 신선함을 표시
      
      // 데이터 캐싱
      cacheData(sitesWithShare, allSitesData);
      
      setLoading(false);
      console.log('Data fetch completed successfully');
    };

    try {
      await fetchLogic();
    } catch (err) {
      console.error('All data fetch attempts failed:', err);
      const errorType = getErrorType(err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      
      setErrorType(errorType);
      setLoading(false);
      
      if (errorType === 'ratelimit') {
        // 429 에러 시 자동 재시도
        await retryWithDelay(fetchLogic, 0);
      } else {
        // 다른 에러의 경우 캐시된 데이터 사용 시도
        if (fallbackData && fallbackData.length > 0) {
          setSites(fallbackData);
          setLastUpdate(`${new Date().toLocaleString()} (캐시된 데이터 사용)`);
          setError('실시간 데이터를 가져올 수 없어 캐시된 데이터를 표시합니다.');
        } else {
          setError(`데이터를 가져올 수 없습니다. ${errorMessage}`);
        }
      }
    }
  };

  const fetchAllSitesStats = async () => {
    try {
      // 먼저 API 서버 시도
      try {
        const response = await axios.get(`${API_BASE_URL}/api/firebase/all_sites_daily_stats/`, {
          timeout: 15000 // 15초 타임아웃 (차트 데이터는 더 오래 걸릴 수 있음)
        });
        setAllSitesData(response.data);
        
        // 차트 데이터도 캐싱
        cacheData(sites, response.data);
        
        console.log('All sites stats loaded from API server');
        return;
      } catch (apiError) {
        console.log('API server failed for stats, trying Firebase direct...', apiError);
        
        // API 실패시 Firebase 직접 연결로 통계 데이터 구성
        const firebaseData = await firebaseService.getAllSitesDailyStats(7);
        setAllSitesData(firebaseData);
        
        // 차트 데이터도 캐싱
        cacheData(sites, firebaseData);
        
        console.log('All sites stats loaded from Firebase directly');
        return;
      }
    } catch (err) {
      console.error('All attempts to fetch stats failed:', err);
      
      // 통계 데이터 실패 시 캐시된 데이터 사용 시도
      try {
        const cachedStats = localStorage.getItem('poker-stats-cache');
        if (cachedStats) {
          const parsedStats = JSON.parse(cachedStats);
          setAllSitesData(parsedStats);
          console.log('Using cached stats data');
        }
      } catch (cacheError) {
        console.warn('Failed to load cached stats:', cacheError);
      }
      
      // 통계 데이터 실패는 차트만 영향받으므로 앱을 중단하지 않음
    }
  };

  const triggerCrawl = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post(`${API_BASE_URL}/api/firebase/crawl_and_save_data/`);
      alert(`크롤링 완료! ${response.data.count}개 사이트 데이터 수집`);
      fetchCurrentRanking(); // 크롤링 후 데이터 새로고침
      fetchAllSitesStats(); // 차트 데이터도 새로고침
    } catch (err) {
      console.error('Error triggering crawl:', err);
      alert('Crawl function is not available when using direct Firebase connection. Crawling is handled by GitHub Actions daily.');
      setLoading(false);
    }
  };

  const getCategoryBadgeColor = (category: string) => {
    return category === 'GG_POKER' ? '#28a745' : '#6c757d';
  };

  const handleSort = useCallback((field: SortField) => {
    setSortField(prevField => {
      if (prevField === field) {
        // 같은 필드를 클릭하면 정렬 방향만 토글
        setSortDirection(prevDirection => prevDirection === 'asc' ? 'desc' : 'asc');
        return prevField;
      } else {
        // 다른 필드를 클릭하면 해당 필드로 변경하고 적절한 기본 방향 설정
        const numericFields: SortField[] = ['rank', 'players_online', 'cash_players', 'peak_24h', 'seven_day_avg', 'players_share', 'cash_share'];
        setSortDirection(numericFields.includes(field) ? 'desc' : 'asc');
        return field;
      }
    });
  }, []);

  const sortedSites = React.useMemo(() => {
    return [...sites].sort((a, b) => {
    let aValue: any = a[sortField];
    let bValue: any = b[sortField];

    // 문자열인 경우 toLowerCase 적용
    if (typeof aValue === 'string') {
      aValue = aValue.toLowerCase();
    }
    if (typeof bValue === 'string') {
      bValue = bValue.toLowerCase();
    }

    if (aValue < bValue) {
      return sortDirection === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortDirection === 'asc' ? 1 : -1;
    }
      return 0;
    });
  }, [sites, sortField, sortDirection]);

  const getSortIcon = useCallback((field: SortField) => {
    if (sortField !== field) {
      return ' ↕'; // 정렬 가능 표시
    }
    return sortDirection === 'asc' ? ' ↑' : ' ↓';
  }, [sortField, sortDirection]);

  // 사용자 친화적 에러 메시지
  const getErrorMessage = () => {
    if (!error) return null;
    
    if (isRetrying) {
      return (
        <div className="error-message retrying">
          🔄 API 요청 한도 초과로 인해 재시도 중입니다... ({retryCount}/3)
          <br />
          <small>잠시만 기다려 주세요. 자동으로 데이터를 다시 가져옵니다.</small>
        </div>
      );
    }
    
    switch (errorType) {
      case 'ratelimit':
        return (
          <div className="error-message rate-limit">
            ⚠️ Firebase API 요청 한도가 초과되었습니다
            <br />
            <small>
              잠시 후 자동으로 재시도됩니다. 또는 새로고침 버튼을 눌러 캐시된 데이터를 확인하세요.
            </small>
            <button 
              onClick={() => {
                firebaseService.clearCache();
                window.location.reload();
              }}
              className="btn btn-small"
              style={{ marginLeft: '10px' }}
            >
              새로고침
            </button>
          </div>
        );
      case 'network':
        return (
          <div className="error-message network">
            🌐 네트워크 연결에 문제가 있습니다
            <br />
            <small>{error}</small>
          </div>
        );
      default:
        return (
          <div className="error-message server">
            🔧 서버에 일시적인 문제가 발생했습니다
            <br />
            <small>{error}</small>
          </div>
        );
    }
  };

  if (loading && sites.length === 0) {
    return (
      <div className="App">
        <header className="App-header">
          <h1>🎰 Online Poker Traffic Analysis</h1>
          <p className="subtitle">Real-time poker site traffic data from PokerScout</p>
        </header>
        <div className="loading">
          <div className="loading-spinner"></div>
          <p>데이터를 불러오는 중...</p>
          {retryCount > 0 && (
            <small>재시도 중... ({retryCount}/3)</small>
          )}
        </div>
      </div>
    );
  }

  return (
    <div className="App">
      <header className="App-header">
        <h1>🎰 Online Poker Traffic Analysis</h1>
        <p className="subtitle">Real-time poker site traffic data from PokerScout</p>
      </header>
      
      <main className="App-main">
        <div className="controls">
          <button 
            onClick={() => debouncedFetch(() => fetchCurrentRanking(true), 500)}
            className="btn btn-refresh"
            disabled={loading || isRetrying}
          >
            🔄 Refresh Data
            {isDataFresh && <span className="cache-indicator">최신</span>}
          </button>
          <button 
            onClick={triggerCrawl}
            className="btn btn-crawl"
            disabled={loading || isRetrying}
          >
            🕷️ Trigger New Crawl
          </button>
          {lastUpdate && (
            <span className="last-update">
              Last updated: {lastUpdate}
              {isDataFresh && <span className="cache-indicator">신선함</span>}
            </span>
          )}
        </div>

        {getErrorMessage()}

        <div className="tabs">
          <button 
            className={`tab ${activeTab === 'table' ? 'active' : ''}`}
            onClick={() => setActiveTab('table')}
          >
            📊 Table View
          </button>
          <button 
            className={`tab ${activeTab === 'charts' ? 'active' : ''}`}
            onClick={() => setActiveTab('charts')}
          >
            📈 Charts View
          </button>
        </div>

        {activeTab === 'table' && (
        <div className="table-container">
          <table className="sites-table">
            <thead>
              <tr>
                <th onClick={() => handleSort('rank')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Rank{getSortIcon('rank')}
                </th>
                <th onClick={() => handleSort('site_name')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Site Name{getSortIcon('site_name')}
                </th>
                <th onClick={() => handleSort('category')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Category{getSortIcon('category')}
                </th>
                <th onClick={() => handleSort('players_online')} style={{ cursor: 'pointer', userSelect: 'none', backgroundColor: sortField === 'players_online' ? '#f0f8ff' : 'transparent' }}>
                  Players Online{getSortIcon('players_online')}
                </th>
                <th onClick={() => handleSort('players_share')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Share %{getSortIcon('players_share')}
                </th>
                <th onClick={() => handleSort('cash_players')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Cash Players{getSortIcon('cash_players')}
                </th>
                <th onClick={() => handleSort('cash_share')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Share %{getSortIcon('cash_share')}
                </th>
                <th onClick={() => handleSort('peak_24h')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  24h Peak{getSortIcon('peak_24h')}
                </th>
                <th onClick={() => handleSort('seven_day_avg')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  7-Day Avg{getSortIcon('seven_day_avg')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedSites.map((site, index) => (
                <tr key={site.site_name} className={site.category === 'GG_POKER' ? 'gg-poker-row' : ''}>
                  <td className="rank">#{site.rank || index + 1}</td>
                  <td className="site-name">{site.site_name}</td>
                  <td>
                    <span 
                      className="category-badge" 
                      style={{ backgroundColor: getCategoryBadgeColor(site.category) }}
                    >
                      {site.category}
                    </span>
                  </td>
                  <td className="number">{site.players_online.toLocaleString()}</td>
                  <td className="number">{site.players_share?.toFixed(2)}%</td>
                  <td className="number">{site.cash_players.toLocaleString()}</td>
                  <td className="number">{site.cash_share?.toFixed(2)}%</td>
                  <td className="number">{site.peak_24h.toLocaleString()}</td>
                  <td className="number">{site.seven_day_avg.toLocaleString()}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        )}

        {activeTab === 'charts' && allSitesData && (
          <div className="charts-container">
            <div className="chart-section">
              <MarketShareStackedChart 
                data={allSitesData.data} 
                metric="players_online"
                title="Players Online - Market Share Distribution (Top 10 Sites)"
              />
            </div>
            
            <div className="chart-section">
              <MarketShareStackedChart 
                data={allSitesData.data} 
                metric="cash_players"
                title="Cash Players - Market Share Distribution (Top 10 Sites)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="players_online"
                title="Players Online - Historical Trend (Top 10 Sites)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="cash_players"
                title="Cash Players - Historical Trend (Top 10 Sites)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="peak_24h"
                title="24h Peak - Historical Trend (Top 10 Sites)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="seven_day_avg"
                title="7-Day Average - Historical Trend (Top 10 Sites)"
              />
            </div>
          </div>
        )}

        <div className="summary">
          <h3>Summary</h3>
          <p>Total Sites: {sites.length}</p>
          <p>GG Poker Sites: {sites.filter(s => s.category === 'GG_POKER').length}</p>
          <p>Total Players Online: {sites.reduce((sum, site) => sum + site.players_online, 0).toLocaleString()}</p>
          <p>GG Poker Market Share: {
            sites.filter(s => s.category === 'GG_POKER')
              .reduce((sum, site) => sum + (site.players_share || 0), 0)
              .toFixed(2)
          }%</p>
        </div>
      </main>
    </div>
  );
}

export default App;