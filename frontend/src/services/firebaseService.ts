/**
 * 간단한 JSON 기반 데이터 서비스
 * Firebase 대신 정적 JSON 파일을 사용
 */

class DataService {
  private cache: Map<string, any> = new Map();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5분 캐시
  
  constructor() {
    console.log('[DataService] Using static JSON data');
  }

  async getCurrentRanking(): Promise<any[]> {
    try {
      // GitHub Pages에서 제공하는 정적 JSON 파일 읽기
      const response = await fetch('/poker-online-analyze/data/latest.json');
      
      if (!response.ok) {
        console.error('[DataService] Failed to fetch data:', response.status);
        return [];
      }
      
      const data = await response.json();
      console.log('[DataService] Loaded data:', data.summary);
      
      // sites 배열 반환 (이미 rank로 정렬됨)
      const sites = data.sites || [];
      
      // last_updated 필드 추가
      return sites.map((site: any) => ({
        ...site,
        last_updated: site.collected_at || data.timestamp
      }));
      
    } catch (error) {
      console.error('[DataService] Error loading data:', error);
      return [];
    }
  }

  async getAllSitesDailyStats(days: number = 7): Promise<any> {
    try {
      // 현재 순위 데이터 가져오기
      const currentRanking = await this.getCurrentRanking();
      
      const allSitesData: any = {
        total_sites: currentRanking.length,
        data: {},
        days: days
      };

      // 각 사이트에 대한 더미 일별 데이터 생성 (실제 일별 데이터가 없으므로)
      currentRanking.forEach(site => {
        allSitesData.data[site.site_name] = {
          daily_data: Array(days).fill(null).map((_, i) => ({
            date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
            players_online: site.players_online + Math.floor(Math.random() * 200 - 100),
            cash_players: site.cash_players + Math.floor(Math.random() * 100 - 50),
            peak_24h: site.peak_24h,
            seven_day_avg: site.seven_day_avg
          })).reverse(),
          current_rank: site.rank,
          category: site.category
        };
      });
      
      return allSitesData;
      
    } catch (error) {
      console.error('[DataService] Error getting daily stats:', error);
      return {
        total_sites: 0,
        data: {},
        days: days
      };
    }
  }

  async getSiteDailyStats(siteName: string, days: number = 7): Promise<any[]> {
    try {
      const allStats = await this.getAllSitesDailyStats(days);
      const siteData = allStats.data[siteName];
      
      if (siteData && siteData.daily_data) {
        return siteData.daily_data;
      }
      
      return [];
    } catch (error) {
      console.error(`[DataService] Error for ${siteName}:`, error);
      return [];
    }
  }

  async getTopSitesByCategory(category: string, limit: number = 10): Promise<any[]> {
    try {
      const allSites = await this.getCurrentRanking();
      
      const filteredSites = category === 'ALL' 
        ? allSites 
        : allSites.filter(site => site.category === category);
      
      return filteredSites.slice(0, limit);
    } catch (error) {
      console.error('[DataService] Error:', error);
      return [];
    }
  }

  clearCache(): void {
    this.cache.clear();
    console.log('[DataService] Cache cleared');
  }
}

// 싱글톤 인스턴스 생성 및 내보내기
const firebaseService = new DataService();
export default firebaseService;