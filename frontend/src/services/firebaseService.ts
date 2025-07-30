/**
 * Firebase 클라이언트 사이드 서비스
 * GitHub Pages에서 직접 Firebase에 연결
 */

// Firebase 클라이언트 라이브러리는 환경에 따라 다르게 처리
// let firebase: any = null; // Currently unused

// 간단한 HTTP 기반 Firebase REST API 클라이언트
class FirebaseRestClient {
  private baseUrl: string;
  
  constructor() {
    // Firebase REST API URL (프로젝트 ID는 환경 변수에서 가져오거나 하드코딩)
    const projectId = process.env.REACT_APP_FIREBASE_PROJECT_ID || 'poker-online-analyze';
    this.baseUrl = `https://firestore.googleapis.com/v1/projects/${projectId}/databases/(default)/documents`;
  }

  async getCurrentRanking(): Promise<any[]> {
    try {
      console.log('Fetching current ranking from Firebase REST API...');
      
      // sites 컬렉션의 모든 문서 가져오기
      const response = await fetch(`${this.baseUrl}/sites`);
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      
      if (!data.documents) {
        return [];
      }

      // Firebase 문서를 앱에서 사용하는 형식으로 변환
      const sites = await Promise.all(
        data.documents.map(async (doc: any) => {
          const siteName = doc.name.split('/').pop();
          
          // 각 사이트의 최신 traffic_logs 가져오기
          const trafficResponse = await fetch(
            `${this.baseUrl}/sites/${encodeURIComponent(siteName)}/traffic_logs`
          );
          
          let latestTraffic = null;
          if (trafficResponse.ok) {
            const trafficData = await trafficResponse.json();
            if (trafficData.documents && trafficData.documents.length > 0) {
              // 최신 데이터 찾기 (collected_at 기준으로 정렬)
              const sortedLogs = trafficData.documents.sort((a: any, b: any) => {
                const dateA = new Date(a.fields?.collected_at?.timestampValue || 0);
                const dateB = new Date(b.fields?.collected_at?.timestampValue || 0);
                return dateB.getTime() - dateA.getTime();
              });
              latestTraffic = sortedLogs[0].fields;
            }
          }
          
          return {
            site_name: siteName,
            category: doc.fields?.category?.stringValue || 'UNKNOWN',
            players_online: latestTraffic?.players_online?.integerValue || 0,
            cash_players: latestTraffic?.cash_players?.integerValue || 0,
            peak_24h: latestTraffic?.peak_24h?.integerValue || 0,
            seven_day_avg: latestTraffic?.seven_day_avg?.integerValue || 0,
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
      return sortedSites;
      
    } catch (error) {
      console.error('Error fetching current ranking:', error);
      throw error;
    }
  }

  async getAllSitesDailyStats(days: number = 7): Promise<any> {
    try {
      console.log(`Fetching all sites daily stats for ${days} days...`);
      
      // 현재 순위 먼저 가져오기
      const currentRanking = await this.getCurrentRanking();
      
      const allSitesData: any = {
        total_sites: currentRanking.length,
        data: {},
        days: days
      };

      // 각 사이트의 실제 일별 데이터 가져오기
      for (const site of currentRanking) {
        try {
          // 실제 traffic_logs 데이터 가져오기
          const trafficResponse = await fetch(
            `${this.baseUrl}/sites/${encodeURIComponent(site.site_name)}/traffic_logs`
          );
          
          let dailyData = [];
          
          if (trafficResponse.ok) {
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
              dailyData = sortedLogs.map((log: any) => {
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
          }
          
          // 데이터가 없으면 현재 값으로 하나의 포인트만 생성
          if (dailyData.length === 0) {
            dailyData = [{
              date: new Date().toISOString(),
              players_online: site.players_online,
              cash_players: site.cash_players,
              peak_24h: site.peak_24h,
              seven_day_avg: site.seven_day_avg
            }];
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
      }

      console.log(`Prepared daily stats for ${currentRanking.length} sites with actual traffic data`);
      return allSitesData;
      
    } catch (error) {
      console.error('Error fetching all sites daily stats:', error);
      throw error;
    }
  }
}

// 글로벌 인스턴스
const firebaseService = new FirebaseRestClient();

export default firebaseService;