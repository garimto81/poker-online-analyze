#!/usr/bin/env python3
"""
GitHub Actions용 개선된 크롤링 스크립트
Firebase 초기화 실패에도 크롤링 진행하도록 수정
"""
import sys
import os
import logging
from datetime import datetime, timezone
import json
import re
import cloudscraper
from bs4 import BeautifulSoup

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firebase Admin SDK 초기화 시도
db = None
try:
    import firebase_admin
    from firebase_admin import credentials, firestore
    
    # GitHub Actions 환경과 로컬 환경 모두 지원
    possible_key_paths = [
        # GitHub Actions 환경
        os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key', 'firebase-service-account-key.json'),
        # 로컬 환경
        os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'key', 'firebase-service-account-key.json'),
    ]
    
    key_path = None
    for path in possible_key_paths:
        if os.path.exists(path):
            key_path = os.path.abspath(path)
            logger.info(f"Firebase 키 파일 발견: {key_path}")
            break
    
    if key_path:
        cred = credentials.Certificate(key_path)
        if not firebase_admin._apps:
            firebase_admin.initialize_app(cred)
        db = firestore.client()
        logger.info("Firebase Admin SDK가 성공적으로 초기화되었습니다.")
    else:
        logger.warning("Firebase 키 파일을 찾을 수 없습니다. Firebase 업로드가 스킵됩니다.")
        
except Exception as e:
    logger.warning(f"Firebase Admin SDK 초기화 실패: {e}")
    logger.warning("Firebase 업로드가 스킵됩니다.")

class LivePokerScoutCrawler:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
        )
        self.gg_poker_sites = ['GGNetwork', 'GGPoker ON', 'GG Poker', 'GGPoker']
        
    def crawl_pokerscout_data(self):
        logger.info("PokerScout 실시간 크롤링 시작...")
        try:
            response = self.scraper.get('https://www.pokerscout.com', timeout=30)
            response.raise_for_status()
            logger.info(f"응답 상태 코드: {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'class': 'rankTable'})
            if not table:
                logger.error("PokerScout 테이블을 찾을 수 없습니다")
                return []
            
            logger.info("rankTable 발견!")
            collected_data = []
            rows = table.find_all('tr')[1:]
            logger.info(f"발견된 행 수: {len(rows)}")
            
            for i, row in enumerate(rows):
                try:
                    if 'cus_top_traffic_coin' in row.get('class', []):
                        continue
                    brand_title = row.find('span', {'class': 'brand-title'})
                    if not brand_title:
                        continue
                    site_name = brand_title.get_text(strip=True)
                    if not site_name or len(site_name) < 2:
                        continue
                    
                    players_online, cash_players, peak_24h, seven_day_avg = 0, 0, 0, 0
                    
                    online_td = row.find('td', {'id': 'online'})
                    if online_td and (span := online_td.find('span')) and (text := span.get_text(strip=True).replace(',', '')) and text.isdigit():
                        players_online = int(text)
                    
                    cash_td = row.find('td', {'id': 'cash'})
                    if cash_td and (text := cash_td.get_text(strip=True).replace(',', '')) and text.isdigit():
                        cash_players = int(text)

                    peak_td = row.find('td', {'id': 'peak'})
                    if peak_td and (span := peak_td.find('span')) and (text := span.get_text(strip=True).replace(',', '')) and text.isdigit():
                        peak_24h = int(text)

                    avg_td = row.find('td', {'id': 'avg'})
                    if avg_td and (span := avg_td.find('span')) and (text := span.get_text(strip=True).replace(',', '')) and text.isdigit():
                        seven_day_avg = int(text)

                    if players_online == 0 and cash_players == 0 and peak_24h == 0:
                        continue
                    
                    site_name = re.sub(r'[^\w\s\-\(\)\.&]', '', site_name).strip()
                    category = 'GG_POKER' if site_name in self.gg_poker_sites else 'COMPETITOR'
                    
                    collected_data.append({
                        'site_name': site_name,
                        'category': category,
                        'players_online': players_online,
                        'cash_players': cash_players,
                        'peak_24h': peak_24h,
                        'seven_day_avg': seven_day_avg,
                        'collected_at': datetime.now(timezone.utc).isoformat()
                    })
                except Exception as e:
                    logger.error(f"행 {i+1} 처리 중 오류: {str(e)}")
                    continue
            
            logger.info(f"크롤링 완료: {len(collected_data)}개 사이트 수집")
            return collected_data
        except Exception as e:
            logger.error(f"크롤링 실패: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return []

def upload_to_firestore_efficiently(data):
    """수집된 데이터를 Firebase에 업로드"""
    if not db:
        logger.warning("Firestore 클라이언트가 초기화되지 않아 업로드를 스킵합니다.")
        return False
    
    if not data:
        logger.warning("업로드할 데이터가 없습니다.")
        return False

    logger.info("Firestore에 데이터 업로드 시작...")
    
    try:
        # Batch Write를 사용하여 여러 작업을 한 번의 요청으로 처리
        batch = db.batch()
        
        for site_data in data:
            site_name = site_data['site_name']
            collected_at_iso = site_data['collected_at']
            
            # 1. `sites` 컬렉션 처리
            site_ref = db.collection('sites').document(site_name)
            site_info = {
                'site_name': site_name,
                'category': site_data['category'],
                'last_updated_at': firestore.SERVER_TIMESTAMP
            }
            batch.set(site_ref, site_info, merge=True)

            # 2. `traffic_logs` 하위 컬렉션 처리
            log_ref = site_ref.collection('traffic_logs').document(collected_at_iso)
            traffic_data = {
                'players_online': site_data['players_online'],
                'cash_players': site_data['cash_players'],
                'peak_24h': site_data['peak_24h'],
                'seven_day_avg': site_data['seven_day_avg'],
                'collected_at': datetime.fromisoformat(collected_at_iso).replace(tzinfo=timezone.utc)
            }
            batch.set(log_ref, traffic_data)

        # Batch 작업 일괄 커밋
        batch.commit()
        logger.info(f"성공적으로 {len(data)}개 사이트의 데이터를 Firestore에 업로드했습니다.")
        return True
        
    except Exception as e:
        logger.error(f"Firestore 업로드 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def save_backup_json(data):
    """Firebase 업로드 실패 시 백업용 JSON 저장"""
    if not data:
        return
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"crawl_backup_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"백업 데이터를 {filename}에 저장했습니다.")
    except Exception as e:
        logger.error(f"백업 저장 실패: {e}")

def run_github_actions_crawl():
    """GitHub Actions에서 실행되는 메인 크롤링 함수"""
    logger.info("=== GitHub Actions Crawling Start ===")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Firebase initialized: {db is not None}")
    
    try:
        # Create crawler instance
        crawler = LivePokerScoutCrawler()
        
        # Crawl data
        logger.info("Starting crawl...")
        crawled_data = crawler.crawl_pokerscout_data()
        
        if crawled_data:
            logger.info(f"Crawl success: {len(crawled_data)} sites found")
            
            # Log first few sites for verification
            for i, site in enumerate(crawled_data[:3]):
                logger.info(f"Sample {i+1}: {site.get('site_name', 'Unknown')} - {site.get('players_online', 0)} players")
            
            # Calculate totals
            total_players = sum(site.get('players_online', 0) for site in crawled_data)
            logger.info(f"Total players online across all sites: {total_players:,}")
            
            # Try to upload to Firebase
            upload_success = upload_to_firestore_efficiently(crawled_data)
            
            if not upload_success:
                # Save backup if Firebase upload failed
                save_backup_json(crawled_data)
            
            return True
        else:
            logger.error("ERROR: No data crawled")
            return False
            
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_github_actions_crawl()
    logger.info("=== Crawling Complete ===")
    sys.exit(0 if success else 1)