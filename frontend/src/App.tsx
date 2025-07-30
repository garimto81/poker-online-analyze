import React, { useState, useEffect } from 'react';
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
  const [lastUpdate, setLastUpdate] = useState<string>('');
  const [allSitesData, setAllSitesData] = useState<AllSitesData | null>(null);
  const [activeTab, setActiveTab] = useState<'table' | 'charts'>('table');
  const [sortField, setSortField] = useState<SortField>('rank');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');

  // API URL 환경 변수 설정 with fallbacks
  const API_BASE_URL = process.env.REACT_APP_API_URL || 
    (process.env.NODE_ENV === 'production' 
      ? 'https://poker-analyzer-api.vercel.app' 
      : 'http://localhost:4001');

  console.log('API_BASE_URL:', API_BASE_URL); // 디버깅용

  useEffect(() => {
    fetchCurrentRanking();
    fetchAllSitesStats();
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const fetchCurrentRanking = async () => {
    try {
      setLoading(true);
      setError(null);
      
      let sitesData: Site[] = [];
      
      // 먼저 API 서버 시도
      try {
        const response = await axios.get(`${API_BASE_URL}/api/firebase/current_ranking/`);
        sitesData = response.data;
        if (response.data.length > 0 && response.data[0].last_updated) {
          setLastUpdate(new Date(response.data[0].last_updated).toLocaleString());
        }
        console.log('Data loaded from API server successfully');
      } catch (apiError) {
        console.log('API server failed, trying Firebase direct connection...', apiError);
        
        // API 실패시 Firebase 직접 연결 시도
        const firebaseData = await firebaseService.getCurrentRanking();
        sitesData = firebaseData;
        if (firebaseData.length > 0 && firebaseData[0].last_updated) {
          setLastUpdate(new Date(firebaseData[0].last_updated).toLocaleString());
        }
        console.log('Data loaded from Firebase directly');
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
      setLoading(false);
    } catch (err) {
      console.error('All data fetch attempts failed:', err);
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to fetch data. Tried API (${API_BASE_URL}) and Firebase direct. Error: ${errorMessage}`);
      setLoading(false);
    }
  };

  const fetchAllSitesStats = async () => {
    try {
      // 먼저 API 서버 시도
      try {
        const response = await axios.get(`${API_BASE_URL}/api/firebase/all_sites_daily_stats/`);
        setAllSitesData(response.data);
        console.log('All sites stats loaded from API server');
        return;
      } catch (apiError) {
        console.log('API server failed for stats, trying Firebase direct...', apiError);
        
        // API 실패시 Firebase 직접 연결로 통계 데이터 구성
        const firebaseData = await firebaseService.getAllSitesDailyStats(7);
        setAllSitesData(firebaseData);
        console.log('All sites stats loaded from Firebase directly');
        return;
      }
    } catch (err) {
      console.error('All attempts to fetch stats failed:', err);
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

  const handleSort = (field: SortField) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  const sortedSites = [...sites].sort((a, b) => {
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

  const getSortIcon = (field: SortField) => {
    if (sortField !== field) {
      return ''; // 정렬되지 않은 상태
    }
    return sortDirection === 'asc' ? '▲' : '▼';
  };

  if (loading) {
    return (
      <div className="App">
        <div className="loading">Loading...</div>
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
          <button onClick={fetchCurrentRanking} className="btn btn-refresh">
            🔄 Refresh Data
          </button>
          <button onClick={triggerCrawl} className="btn btn-crawl">
            🕷️ Trigger New Crawl
          </button>
          {lastUpdate && (
            <span className="last-update">Last updated: {lastUpdate}</span>
          )}
        </div>

        {error && (
          <div className="error-message">
            ⚠️ {error}
          </div>
        )}

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
                <th onClick={() => handleSort('rank')} style={{ cursor: 'pointer' }}>
                  Rank {getSortIcon('rank')}
                </th>
                <th onClick={() => handleSort('site_name')} style={{ cursor: 'pointer' }}>
                  Site Name {getSortIcon('site_name')}
                </th>
                <th onClick={() => handleSort('category')} style={{ cursor: 'pointer' }}>
                  Category {getSortIcon('category')}
                </th>
                <th onClick={() => handleSort('players_online')} style={{ cursor: 'pointer' }}>
                  Players Online {getSortIcon('players_online')}
                </th>
                <th onClick={() => handleSort('players_share')} style={{ cursor: 'pointer' }}>
                  Share % {getSortIcon('players_share')}
                </th>
                <th onClick={() => handleSort('cash_players')} style={{ cursor: 'pointer' }}>
                  Cash Players {getSortIcon('cash_players')}
                </th>
                <th onClick={() => handleSort('cash_share')} style={{ cursor: 'pointer' }}>
                  Share % {getSortIcon('cash_share')}
                </th>
                <th onClick={() => handleSort('peak_24h')} style={{ cursor: 'pointer' }}>
                  24h Peak {getSortIcon('peak_24h')}
                </th>
                <th onClick={() => handleSort('seven_day_avg')} style={{ cursor: 'pointer' }}>
                  7-Day Avg {getSortIcon('seven_day_avg')}
                </th>
              </tr>
            </thead>
            <tbody>
              {sortedSites.map((site, index) => (
                <tr key={site.site_name} className={site.category === 'GG_POKER' ? 'gg-poker-row' : ''}>
                  <td className="rank">#{sortField === 'rank' && sortDirection === 'asc' ? site.rank : index + 1}</td>
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