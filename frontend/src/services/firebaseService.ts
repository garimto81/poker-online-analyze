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
    console.log('[Firebase] Initialize with project ID:', projectId);
  }

  // 캐시 확인 및 반환
  private getFromCache(key: string): any | null {
    const cached = this.cache.get(key);
    if (cached && Date.now() < cached.expiry) {
      console.log(`[Cache] Hit for key: ${key}`);
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
          console.log(`[API] Rate limited (429). Retrying in ${delay}ms... (${retries + 1}/${this.MAX_RETRIES})`);
          await new Promise(resolve => setTimeout(resolve, delay));
          return this.fetchWithRetry(url, retries + 1);
        } else {
          throw new Error(`Rate limit exceeded after ${this.MAX_RETRIES} retries`);
        }
      }
      
      if (!response.ok && response.status !== 404) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      return response;
    } catch (error) {
      if (retries < this.MAX_RETRIES) {
        const delay = this.RETRY_DELAY * Math.pow(2, retries);
        console.log(`[API] Network error. Retrying in ${delay}ms... (${retries + 1}/${this.MAX_RETRIES})`);
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
          console.error('[Queue] Request failed:', error);
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

  // 데모 데이터 반환 (최종 fallback)
  private getDemoData(): any[] {
    console.log('[Firebase] Returning demo data as final fallback');
    return [
      {
        rank: 1,
        site_name: 'WPT Global',
        category: 'WPT',
        players_online: 5219,
        cash_players: 1694,
        peak_24h: 3825,
        seven_day_avg: 2400,
        last_updated: new Date().toISOString()
      },
      {
        rank: 2,
        site_name: 'IDNPoker',
        category: 'COMPETITOR',
        players_online: 5528,
        cash_players: 1400,
        peak_24h: 2366,
        seven_day_avg: 1450,
        last_updated: new Date().toISOString()
      },
      {
        rank: 7,
        site_name: 'GGPoker ON',
        category: 'GG_POKER',
        players_online: 2737,
        cash_players: 532,
        peak_24h: 679,
        seven_day_avg: 375,
        last_updated: new Date().toISOString()
      },
      {
        rank: 9,
        site_name: 'Chico Poker',
        category: 'COMPETITOR',
        players_online: 2217,
        cash_players: 451,
        peak_24h: 573,
        seven_day_avg: 375,
        last_updated: new Date().toISOString()
      },
      {
        rank: 33,
        site_name: 'GGNetwork',
        category: 'GG_POKER',
        players_online: 153008,
        cash_players: 10404,
        peak_24h: 13603,
        seven_day_avg: 0,
        last_updated: new Date().toISOString()
      }
    ];
  }

  async getCurrentRanking(): Promise<any[]> {
    const cacheKey = 'current_ranking';
    
    // 캐시 확인
    const cachedData = this.getFromCache(cacheKey);
    if (cachedData) {
      console.log('[Cache] Returning cached ranking data');
      return cachedData;
    }

    // 여러 프로젝트 ID로 시도
    const projectIds = [
      process.env.REACT_APP_FIREBASE_PROJECT_ID,
      'poker-online-analyze',
      'poker-analyzer-ggp',
      'poker-analyzer-api'
    ].filter(Boolean);

    console.log('[Firebase] Trying multiple project IDs:', projectIds);

    for (const projectId of projectIds) {
      try {
        const testUrl = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents/sites`;
        console.log(`[Firebase] Trying project: ${projectId}`);
        
        // sites 컬렉션의 모든 문서 가져오기
        const response = await this.fetchWithRetry(testUrl);
        
        if (response.status === 404) {
          console.log(`[Firebase] Project not found: ${projectId}`);
          continue;
        }

        const data = await response.json();
        
        if (!data.documents || data.documents.length === 0) {
          console.log(`[Firebase] No documents in project: ${projectId}`);
          continue;
        }

        console.log(`[Firebase] SUCCESS! Connected to: ${projectId} with ${data.documents.length} sites`);
        this.baseUrl = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents`;

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
                  // traffic 데이터를 캐시에 저장
                  this.setCache(trafficCacheKey, latestFields);
                  return latestFields;
                }
                return null;
              } catch (trafficError) {
                console.warn(`[Traffic] Failed for ${siteName}:`, trafficError);
                return null;
              }
            });
            
            // rank 필드가 있으면 사용, 없으면 999
            const rank = doc.fields?.rank?.integerValue ? 
              parseInt(doc.fields.rank.integerValue) : 999;
            
            return {
              site_name: siteName,
              category: doc.fields?.category?.stringValue || 'UNKNOWN',
              rank: rank,
              players_online: parseInt(latestTraffic?.players_online?.integerValue || '0'),
              cash_players: parseInt(latestTraffic?.cash_players?.integerValue || '0'),
              peak_24h: parseInt(latestTraffic?.peak_24h?.integerValue || '0'),
              seven_day_avg: parseInt(latestTraffic?.seven_day_avg?.integerValue || '0'),
              last_updated: latestTraffic?.collected_at?.timestampValue || null
            };
          })
        );

        // rank 필드로 정렬 (크롤러에서 설정한 순위 사용)
        const sortedSites = sites.sort((a, b) => a.rank - b.rank);

        console.log(`[Firebase] Fetched ${sortedSites.length} sites successfully`);
        
        // 결과를 캐시에 저장
        this.setCache(cacheKey, sortedSites);
        
        return sortedSites;

      } catch (error) {
        console.error(`[Firebase] Failed with ${projectId}:`, error);
        continue;
      }
    }

    // 모든 프로젝트 ID 실패 시 데모 데이터 반환
    console.error('[Firebase] All attempts failed, using demo data');
    const demoData = this.getDemoData();
    this.setCache(cacheKey, demoData);
    return demoData;
  }

  async getAllSitesDailyStats(days: number = 7): Promise<any> {
    const cacheKey = `all_sites_daily_stats_${days}`;
    
    // 캐시 확인
    const cachedData = this.getFromCache(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    try {
      console.log(`[Stats] Fetching daily stats for ${days} days...`);
      
      // 현재 순위 먼저 가져오기 (캐시된 데이터 활용 가능)
      const currentRanking = await this.getCurrentRanking();
      
      const allSitesData: any = {
        total_sites: currentRanking.length,
        data: {},
        days: days
      };

      // 데모 데이터인 경우 간단한 통계만 반환
      if (currentRanking.length <= 5) {
        console.log('[Stats] Using simplified stats for demo data');
        
        currentRanking.forEach(site => {
          allSitesData.data[site.site_name] = {
            daily_data: Array(days).fill(null).map((_, i) => ({
              date: new Date(Date.now() - i * 24 * 60 * 60 * 1000).toISOString(),
              players_online: site.players_online + Math.floor(Math.random() * 100 - 50),
              cash_players: site.cash_players + Math.floor(Math.random() * 50 - 25),
              peak_24h: site.peak_24h,
              seven_day_avg: site.seven_day_avg
            })),
            current_rank: site.rank,
            category: site.category
          };
        });
        
        this.setCache(cacheKey, allSitesData);
        return allSitesData;
      }

      // 실제 데이터 처리 (기존 로직)
      await Promise.all(
        currentRanking.map(async (site) => {
          await this.queueRequest(async () => {
            try {
              const trafficResponse = await this.fetchWithRetry(
                `${this.baseUrl}/sites/${encodeURIComponent(site.site_name)}/traffic_logs`
              );
              
              const trafficData = await trafficResponse.json();
              const logs = trafficData.documents || [];
              
              if (logs.length > 0) {
                const sortedLogs = logs.sort((a: any, b: any) => {
                  const dateA = new Date(a.fields?.collected_at?.timestampValue || 0);
                  const dateB = new Date(b.fields?.collected_at?.timestampValue || 0);
                  return dateB.getTime() - dateA.getTime();
                });
                
                const dailyData = sortedLogs.slice(0, days).map((log: any) => {
                  const fields = log.fields || {};
                  return {
                    date: fields.collected_at?.timestampValue || new Date().toISOString(),
                    players_online: parseInt(fields.players_online?.integerValue || '0'),
                    cash_players: parseInt(fields.cash_players?.integerValue || '0'),
                    peak_24h: parseInt(fields.peak_24h?.integerValue || '0'),
                    seven_day_avg: parseInt(fields.seven_day_avg?.integerValue || '0')
                  };
                });
                
                allSitesData.data[site.site_name] = {
                  daily_data: dailyData,
                  current_rank: site.rank,
                  category: site.category
                };
              }
            } catch (error) {
              console.warn(`[Stats] Failed for ${site.site_name}:`, error);
              allSitesData.data[site.site_name] = {
                daily_data: [],
                current_rank: site.rank,
                category: site.category
              };
            }
          });
        })
      );

      this.setCache(cacheKey, allSitesData);
      return allSitesData;

    } catch (error) {
      console.error('[Stats] Error:', error);
      return {
        total_sites: 0,
        data: {},
        days: days
      };
    }
  }

  async getSiteDailyStats(siteName: string, days: number = 7): Promise<any[]> {
    const cacheKey = `site_daily_stats_${siteName}_${days}`;
    
    const cachedData = this.getFromCache(cacheKey);
    if (cachedData) {
      return cachedData;
    }

    try {
      const allStats = await this.getAllSitesDailyStats(days);
      const siteData = allStats.data[siteName];
      
      if (siteData && siteData.daily_data) {
        this.setCache(cacheKey, siteData.daily_data);
        return siteData.daily_data;
      }
      
      return [];
    } catch (error) {
      console.error(`[Site Stats] Error for ${siteName}:`, error);
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
      console.error('[Category] Error:', error);
      return [];
    }
  }
}

// 싱글톤 인스턴스 생성 및 내보내기
const firebaseService = new FirebaseRestClient();
export default firebaseService;