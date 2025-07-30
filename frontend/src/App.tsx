import React, { useState, useEffect } from 'react';
import axios from 'axios';
import TrendChart from './components/TrendChart';
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

type SortField = 'rank' | 'site_name' | 'category' | 'players_online' | 'cash_players' | 'peak_24h' | 'seven_day_avg';
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

  useEffect(() => {
    fetchCurrentRanking();
    fetchAllSitesStats();
  }, []);

  const fetchCurrentRanking = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.get('http://localhost:4001/api/firebase/current_ranking/');
      setSites(response.data);
      if (response.data.length > 0 && response.data[0].last_updated) {
        setLastUpdate(new Date(response.data[0].last_updated).toLocaleString());
      }
      setLoading(false);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError('Failed to fetch data. Please ensure the backend is running.');
      setLoading(false);
    }
  };

  const fetchAllSitesStats = async () => {
    try {
      // 먼저 전체 사이트 데이터 API 시도
      const response = await axios.get('http://localhost:4001/api/firebase/all_sites_daily_stats/');
      setAllSitesData(response.data);
    } catch (err) {
      console.error('Error fetching all sites stats:', err);
      
      // 대안: 전체 사이트 현재 순위를 가져와서 각 사이트별 통계 구성
      try {
        // 1. 전체 사이트 현재 순위 가져오기
        const rankingResponse = await axios.get('http://localhost:4001/api/firebase/current_ranking/');
        const allSites = rankingResponse.data;
        
        // 2. 각 사이트별 일별 데이터는 간단히 현재 값으로 채우기 (임시)
        const allSitesData: AllSitesData = {
          total_sites: allSites.length,
          data: {},
          days: 7
        };
        
        // 3. 각 사이트 데이터 구성
        for (const site of allSites) {
          const dailyData = [];
          // 최근 7일간 데이터 (현재 값으로 채우기)
          for (let i = 0; i < 7; i++) {
            const date = new Date();
            date.setDate(date.getDate() - i);
            dailyData.push({
              date: date.toISOString(),
              players_online: site.players_online,
              cash_players: site.cash_players,
              peak_24h: site.peak_24h,
              seven_day_avg: site.seven_day_avg
            });
          }
          
          allSitesData.data[site.site_name] = {
            current_stats: {
              site_name: site.site_name,
              category: site.category,
              players_online: site.players_online,
              cash_players: site.cash_players,
              peak_24h: site.peak_24h,
              seven_day_avg: site.seven_day_avg
            },
            daily_data: dailyData
          };
        }
        
        setAllSitesData(allSitesData);
        console.log('Using current ranking data for all sites - daily trends will be flat');
      } catch (fallbackErr) {
        console.error('Failed to fetch current ranking:', fallbackErr);
        
        // 최후의 대안: top10 API 사용
        try {
          const response = await axios.get('http://localhost:4001/api/firebase/top10_daily_stats/');
          if (response.data) {
            const convertedData: AllSitesData = {
              total_sites: response.data.top10_sites.length,
              data: response.data.data,
              days: response.data.days
            };
            setAllSitesData(convertedData);
            console.warn('Using limited top10 API - charts will show incorrect rankings!');
          }
        } catch (lastErr) {
          console.error('All API attempts failed:', lastErr);
        }
      }
    }
  };

  const triggerCrawl = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await axios.post('http://localhost:4001/api/firebase/crawl_and_save_data/');
      alert(`크롤링 완료! ${response.data.count}개 사이트 데이터 수집`);
      fetchCurrentRanking(); // 크롤링 후 데이터 새로고침
      fetchAllSitesStats(); // 차트 데이터도 새로고침
    } catch (err) {
      console.error('Error triggering crawl:', err);
      setError('Failed to trigger crawl. Please check the backend.');
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
                <th onClick={() => handleSort('cash_players')} style={{ cursor: 'pointer' }}>
                  Cash Players {getSortIcon('cash_players')}
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
                  <td className="number">{site.cash_players.toLocaleString()}</td>
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
              <TrendChart 
                data={allSitesData.data} 
                metric="players_online"
                title="Players Online - Daily Trend (Top 10 by Current Players Online)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="cash_players"
                title="Cash Players - Daily Trend (Top 10 by Current Cash Players)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="peak_24h"
                title="24h Peak - Daily Trend (Top 10 by Current 24h Peak)"
              />
            </div>
            
            <div className="chart-section">
              <TrendChart 
                data={allSitesData.data} 
                metric="seven_day_avg"
                title="7-Day Average - Daily Trend (Top 10 by Current 7-Day Average)"
              />
            </div>
          </div>
        )}

        <div className="summary">
          <h3>Summary</h3>
          <p>Total Sites: {sites.length}</p>
          <p>GG Poker Sites: {sites.filter(s => s.category === 'GG_POKER').length}</p>
          <p>Total Players Online: {sites.reduce((sum, site) => sum + site.players_online, 0).toLocaleString()}</p>
        </div>
      </main>
    </div>
  );
}

export default App;