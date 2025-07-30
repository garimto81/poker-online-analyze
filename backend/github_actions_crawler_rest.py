#!/usr/bin/env python3
"""
GitHub Actions용 Firebase REST API 크롤러
서비스 계정 키 없이 Firebase 프로젝트 ID만으로 데이터 업로드
"""
import sys
import os
import logging
from datetime import datetime, timezone
import json
import re
import cloudscraper
from bs4 import BeautifulSoup
import requests

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firebase 프로젝트 설정
FIREBASE_PROJECT_ID = "poker-online-analyze"
FIREBASE_DATABASE_URL = f"https://{FIREBASE_PROJECT_ID}-default-rtdb.firebaseio.com"

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

def upload_to_firebase_rest(data):
    """Firebase REST API를 사용하여 데이터 업로드 (인증 없이)"""
    if not data:
        logger.warning("업로드할 데이터가 없습니다.")
        return False
    
    logger.info("Firebase REST API로 데이터 업로드 시작...")
    
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    
    try:
        # 전체 데이터를 한 번에 업로드
        url = f"{FIREBASE_DATABASE_URL}/crawl_data/{timestamp}.json"
        
        # 데이터 구조화
        upload_data = {
            'collected_at': datetime.now(timezone.utc).isoformat(),
            'total_sites': len(data),
            'sites': {}
        }
        
        # 사이트별 데이터 추가
        for site in data:
            site_key = site['site_name'].replace('.', '_').replace('/', '_')
            upload_data['sites'][site_key] = site
        
        # Firebase에 업로드
        response = requests.put(url, json=upload_data)
        
        if response.status_code == 200:
            logger.info(f"성공적으로 {len(data)}개 사이트의 데이터를 Firebase에 업로드했습니다.")
            logger.info(f"업로드 위치: /crawl_data/{timestamp}")
            return True
        else:
            logger.error(f"Firebase 업로드 실패: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Firebase REST API 업로드 중 오류 발생: {e}")
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
    logger.info("=== GitHub Actions REST API Crawling Start ===")
    logger.info(f"Current directory: {os.getcwd()}")
    logger.info(f"Firebase Database URL: {FIREBASE_DATABASE_URL}")
    
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
            
            # Upload to Firebase using REST API
            upload_success = upload_to_firebase_rest(crawled_data)
            
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