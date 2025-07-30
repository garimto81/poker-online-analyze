#!/usr/bin/env python3
"""
크롤링 기능만 테스트하는 스크립트
Firebase 연결 없이 크롤링이 정상 작동하는지 확인
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime, timezone
import logging
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class TestPokerScoutCrawler:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
        )
        self.gg_poker_sites = ['GGNetwork', 'GGPoker ON', 'GG Poker', 'GGPoker']
        
    def crawl_pokerscout_data(self):
        logger.info("PokerScout 크롤링 테스트 시작...")
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

if __name__ == "__main__":
    crawler = TestPokerScoutCrawler()
    data = crawler.crawl_pokerscout_data()
    
    if data:
        logger.info("\n=== 크롤링 결과 ===")
        logger.info(f"총 {len(data)}개 사이트 수집됨")
        
        # 상위 5개 사이트 표시
        logger.info("\n상위 5개 사이트:")
        for i, site in enumerate(data[:5], 1):
            logger.info(f"{i}. {site['site_name']}: {site['players_online']:,} players")
        
        # 전체 플레이어 수 계산
        total_players = sum(site['players_online'] for site in data)
        logger.info(f"\n전체 온라인 플레이어 수: {total_players:,}")
    else:
        logger.error("크롤링 실패: 데이터를 수집할 수 없습니다")