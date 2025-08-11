/**
 * 최적화된 Firebase 클라이언트 사이드 서비스
 * GitHub Pages에서 직접 Firebase에 연결
 * API 할당량 관리 및 캐싱 기능 포함
 */

// 캐시 인터페이스
interface CacheData {
  data: any;
  timestamp: number;
  expiry: number;
}

// 간단한 HTTP 기반 Firebase REST API 클라이언트 (최적화 버전)
class FirebaseRestClient {
  private baseUrl: string;
  private cache: Map<string, CacheData> = new Map();
  private readonly CACHE_DURATION = 5 * 60 * 1000; // 5분 캐시
  private readonly MAX_RETRIES = 3;
  private readonly RETRY_DELAY = 1000; // 1초
  private requestQueue: Array<() => Promise<any>> = [];
  private isProcessingQueue = false;
  
  constructor() {
    // Firebase REST API URL (프로젝트 ID는 환경 변수에서 가져오거나 하드코딩)
    const projectId = process.env.REACT_APP_FIREBASE_PROJECT_ID || 'poker-online-analyze';
    this.baseUrl = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents`;
  }

  // 캐시 확인 및 반환
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expiry) {
      console.log(`Cache hit for key: ${key}`);
      return cached.data;
    }
    if (cached) {
      this.cache.delete(key);
    }
    return null;
  }

  // 캐시에 데이터 저장
  private setCache(key: string, data: any): void {
    this.cache.set(key, {
      data,
      timestamp: Date.now(),
      expiry: Date.now() + this.CACHE_DURATION
    });
  }

  // 429 에러 처리를 위한 재시도 로직이 포함된 fetch
  private async fetchWithRetry(url: string, retries = 0): Promise<Response> {
    try {
      const response = await fetch(url);
      
      if (response.status === 429) {
        if (retries < this.MAX_RETRIES) {
          const delay = this.RETRY_DELAY * Math.pow(2, retries); // 지수 백오프
          console.log(`Rate limited (429). Retrying in ${delay}ms... (${retries + 1}/${this.MAX_RETRIES})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.fetchWithRetry(url, retries + 1);
        } else {
          throw new Error(`Rate limit exceeded after ${this.MAX_RETRIES} retries`);
        }
      }
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response;
    } catch (error) {
      if (retries < this.MAX_RETRIES && (error as Error).message.includes('429')) {
        const delay = this.RETRY_DELAY * Math.pow(2, retries);
        console.log(`Network error (likely 429). Retrying in ${delay}ms... (${retries + 1}/${this.MAX_RETRIES})`);
        await new Promise(resolve => setTimeout(resolve, delay));
        return this.fetchWithRetry(url, retries + 1);
      }
      throw error;
    }
  }

  // 요청 큐 처리 (순차 실행으로 API 호출 제한)
  private async processQueue(): Promise<void> {
    if (this.isProcessingQueue || this.requestQueue.length === 0) return;
    
    this.isProcessingQueue = true;
    
    while (this.requestQueue.length > 0) {
      const request = this.requestQueue.shift();
      if (request) {
        try {
          await request();
          // 요청 간 짧은 지연
          await new Promise(resolve => setTimeout(resolve, 100));
        } catch (error) {
          console.error('Queue request failed:', error);
        }
      }
    }
    
    this.isProcessingQueue = false;
  }

  // 큐에 요청 추가
  private queueRequest<T>(request: () => Promise<T>): Promise<T> {
    return new Promise((resolve, reject) => {
      this.requestQueue.push(async () => {
        try {
          const result = await request();
          resolve(result);
        } catch (error) {
          reject(error);
        }
      });
      this.processQueue();
    });
  }

  async getCurrentRanking(): Promise<any[]> {
    const cacheKey = 'current_ranking';
    
    // 캐시 확인
    const cachedData = this.getFromCache(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    try {
      console.log('Fetching current ranking from Firebase REST API...');
      
      // sites 컬렉션의 모든 문서 가져오기 (재시도 로직 포함)
      const response = await this.fetchWithRetry(`${this.baseUrl}/sites`);
      const data = await response.json();
      
      if (!data.documents) {
        const emptyResult: any[] = [];
        this.setCache(cacheKey, emptyResult);
        return emptyResult;
      }

      // 배치 처리: 모든 사이트의 traffic_logs를 병렬로 가져오되, 큐를 통해 제한
      const sites = await Promise.all(
        data.documents.map(async (doc: any) => {
          const siteName = doc.name.split('/').pop();
          
          // 큐를 통해 traffic_logs 가져오기 (API 호출 제한)
          const latestTraffic = await this.queueRequest(async () => {
            const trafficCacheKey = `traffic_logs_${siteName}`;
            const cachedTraffic = this.getFromCache(trafficCacheKey);
            
            if (cachedTraffic) {
              return cachedTraffic;
            }

            try {
              const trafficResponse = await this.fetchWithRetry(
                `${this.baseUrl}/sites/${encodeURIComponent(siteName)}/traffic_logs`
              );
              
              const trafficData = await trafficResponse.json();
              
              if (trafficData.documents && trafficData.documents.length > 0) {
                // 최신 데이터 찾기 (collected_at 기준으로 정렬)
                const sortedLogs = trafficData.documents.sort((a: any, b: any) => {
                  const dateA = new Date(a.fields?.collected_at?.timestampValue || 0);
                  const dateB = new Date(b.fields?.collected_at?.timestampValue || 0);
                  return dateB.getTime() - dateA.getTime();
                });
                
                const latestFields = sortedLogs[0].fields;
                // traffic 데이터를 캐시에 저장 (더 긴 캐시 시간)
                this.setCache(trafficCacheKey, latestFields);
                return latestFields;
              }
              return null;
            } catch (trafficError) {
              console.warn(`Failed to fetch traffic logs for ${siteName}:`, trafficError);
              return null;
            }
          });
          
          return {
            site_name: siteName,
            category: doc.fields?.category?.stringValue || 'UNKNOWN',
            players_online: parseInt(latestTraffic?.players_online?.integerValue || '0'),
            cash_players: parseInt(latestTraffic?.cash_players?.integerValue || '0'),
            peak_24h: parseInt(latestTraffic?.peak_24h?.integerValue || '0'),
            seven_day_avg: parseInt(latestTraffic?.seven_day_avg?.integerValue || '0'),
            last_updated: latestTraffic?.collected_at?.timestampValue || null
          };
        })
      );

      // players_online으로 정렬하고 순위 추가
      const sortedSites = sites
        .sort((a, b) => b.players_online - a.players_online)
        .map((site, index) => ({
          ...site,
          rank: index + 1
        }));

      console.log(`Fetched ${sortedSites.length} sites from Firebase`);
      
      // 결과를 캐시에 저장
      this.setCache(cacheKey, sortedSites);
      
      return sortedSites;
      
    } catch (error) {
      console.error('Error fetching current ranking:', error);
      throw error;
    }
  }

  async getAllSitesDailyStats(days: number = 7): Promise<any> {
    const cacheKey = `all_sites_daily_stats_${days}`;
    
    // 캐시 확인
    const cachedData = this.getFromCache(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    try {
      console.log(`Fetching all sites daily stats for ${days} days...`);
      
      // 현재 순위 먼저 가져오기 (캐시된 데이터 활용 가능)
      const currentRanking = await this.getCurrentRanking();
      
      const allSitesData: any = {
        total_sites: currentRanking.length,
        data: {},
        days: days
      };

      // 각 사이트의 실제 일별 데이터 가져오기 - 큐 시스템으로 최적화
      await Promise.all(
        currentRanking.map(async (site) => {
          await this.queueRequest(async () => {
            try {
              const dailyDataCacheKey = `daily_data_${site.site_name}_${days}`;
              let dailyData = this.getFromCache(dailyDataCacheKey);
              
              if (!dailyData) {
                // 실제 traffic_logs 데이터 가져오기
                try {
                  const trafficResponse = await this.fetchWithRetry(
                    `${this.baseUrl}/sites/${encodeURIComponent(site.site_name)}/traffic_logs`
                  );
                  
                  const trafficData = await trafficResponse.json();
                  const logs = trafficData.documents || [];
                  
                  if (logs.length > 0) {
                    // 날짜별로 정렬 (최신순)
                    const sortedLogs = logs.sort((a: any, b: any) => {
                      const dateA = new Date(a.fields?.collected_at?.timestampValue || 0);
                      const dateB = new Date(b.fields?.collected_at?.timestampValue || 0);
                      return dateB.getTime() - dateA.getTime();
                    });
                    
                    // 실제 데이터를 daily_data로 변환
                    dailyData = sortedLogs.slice(0, days).map((log: any) => {
                      const fields = log.fields || {};
                      return {
                        date: fields.collected_at?.timestampValue || new Date().toISOString(),
                        players_online: parseInt(fields.players_online?.integerValue || '0'),
                        cash_players: parseInt(fields.cash_players?.integerValue || '0'),
                        peak_24h: parseInt(fields.peak_24h?.integerValue || '0'),
                        seven_day_avg: parseInt(fields.seven_day_avg?.integerValue || '0')
                      };
                    });
                  }
                } catch (trafficError) {
                  console.warn(`Failed to fetch traffic logs for ${site.site_name}:`, trafficError);
                  dailyData = [];
                }

                // 데이터가 없으면 현재 값으로 하나의 포인트만 생성
                if (!dailyData || dailyData.length === 0) {
                  dailyData = [{
                    date: new Date().toISOString(),
                    players_online: site.players_online,
                    cash_players: site.cash_players,
                    peak_24h: site.peak_24h,
                    seven_day_avg: site.seven_day_avg
                  }];
                }
                
                // daily 데이터 캐시 저장
                this.setCache(dailyDataCacheKey, dailyData);
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
              
            } catch (siteError) {
              console.warn(`Error fetching data for ${site.site_name}:`, siteError);
              
              // 에러 시 현재 값으로 하나의 포인트만 생성
              allSitesData.data[site.site_name] = {
                current_stats: {
                  site_name: site.site_name,
                  category: site.category,
                  players_online: site.players_online,
                  cash_players: site.cash_players,
                  peak_24h: site.peak_24h,
                  seven_day_avg: site.seven_day_avg
                },
                daily_data: [{
                  date: new Date().toISOString(),
                  players_online: site.players_online,
                  cash_players: site.cash_players,
                  peak_24h: site.peak_24h,
                  seven_day_avg: site.seven_day_avg
                }]
              };
            }
          });
        })
      );

      console.log(`Prepared daily stats for ${currentRanking.length} sites with actual traffic data`);
      
      // 전체 결과를 캐시에 저장
      this.setCache(cacheKey, allSitesData);
      
      return allSitesData;
      
    } catch (error) {
      console.error('Error fetching all sites daily stats:', error);
      throw error;
    }
  }

  // 캐시 수동 초기화
  public clearCache(): void {
    this.cache.clear();
    console.log('Firebase service cache cleared');
  }

  // 특정 키의 캐시 제거
  public clearCacheKey(key: string): void {
    this.cache.delete(key);
    console.log(`Cache cleared for key: ${key}`);
  }

  // 캐시 상태 확인
  public getCacheStatus(): { size: number; keys: string[] } {
    return {
      size: this.cache.size,
      keys: Array.from(this.cache.keys())
    };
  }

  // 만료된 캐시 정리
  public cleanExpiredCache(): void {
    const now = Date.now();
    let cleanedCount = 0;
    
    Array.from(this.cache.entries()).forEach(([key, data]) => {
      if (now >= data.expiry) {
        this.cache.delete(key);
        cleanedCount++;
      }
    });
    
    console.log(`Cleaned ${cleanedCount} expired cache entries`);
  }
}

// 글로벌 인스턴스
const firebaseService = new FirebaseRestClient();

// 자동 캐시 정리 (10분마다)
setInterval(() => {
  firebaseService.cleanExpiredCache();
}, 10 * 60 * 1000);

export default firebaseService;