#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PokerScout 실시간 크롤링 실행 및 결과 표시
online_data_collector.py와 동일한 로직으로 전체 사이트 크롤링
"""

import cloudscraper
from bs4 import BeautifulSoup
import json
from datetime import datetime
import logging
import sys
import re

# 로깅 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LivePokerScoutCrawler:
    def __init__(self):
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'linux', 'mobile': False}
        )
        # GG 포커 사이트 식별용 (online_data_collector.py와 동일)
        self.gg_poker_sites = ['GGNetwork', 'GGPoker ON', 'GG Poker', 'GGPoker']
        
    def crawl_pokerscout_data(self):
        """PokerScout 크롤링 - online_data_collector.py와 동일한 로직"""
        logger.info("PokerScout 실시간 크롤링 시작...")
        
        try:
            # 1. 웹사이트 접속
            logger.info("https://www.pokerscout.com 접속 중...")
            response = self.scraper.get('https://www.pokerscout.com', timeout=30)
            response.raise_for_status()
            logger.info(f"응답 상태 코드: {response.status_code}")
            
            # 2. HTML 파싱
            soup = BeautifulSoup(response.content, 'html.parser')
            table = soup.find('table', {'class': 'rankTable'})
            
            if not table:
                logger.error("PokerScout 테이블을 찾을 수 없습니다")
                return []
            
            logger.info("rankTable 발견!")
            
            # 3. 데이터 추출
            collected_data = []
            rows = table.find_all('tr')[1:]  # Skip header
            logger.info(f"발견된 행 수: {len(rows)}")
            
            for i, row in enumerate(rows):
                try:
                    # CoinPoker 광고 행은 건너뛰기
                    if 'cus_top_traffic_coin' in row.get('class', []):
                        continue
                    
                    # 사이트명 추출
                    brand_title = row.find('span', {'class': 'brand-title'})
                    if not brand_title:
                        continue
                    
                    site_name = brand_title.get_text(strip=True)
                    if not site_name or len(site_name) < 2:
                        continue
                    
                    # 각 데이터 필드를 ID로 직접 찾기
                    players_online = 0
                    cash_players = 0
                    peak_24h = 0
                    seven_day_avg = 0
                    
                    # Players Online
                    online_td = row.find('td', {'id': 'online'})
                    if online_td:
                        online_span = online_td.find('span')
                        if online_span:
                            online_text = online_span.get_text(strip=True).replace(',', '')
                            if online_text.isdigit():
                                players_online = int(online_text)
                    
                    # Cash Players
                    cash_td = row.find('td', {'id': 'cash'})
                    if cash_td:
                        cash_text = cash_td.get_text(strip=True).replace(',', '')
                        if cash_text.isdigit():
                            cash_players = int(cash_text)
                    
                    # 24H Peak
                    peak_td = row.find('td', {'id': 'peak'})
                    if peak_td:
                        peak_span = peak_td.find('span')
                        if peak_span:
                            peak_text = peak_span.get_text(strip=True).replace(',', '')
                            if peak_text.isdigit():
                                peak_24h = int(peak_text)
                    
                    # 7 Day Average
                    avg_td = row.find('td', {'id': 'avg'})
                    if avg_td:
                        avg_span = avg_td.find('span')
                        if avg_span:
                            avg_text = avg_span.get_text(strip=True).replace(',', '')
                            if avg_text.isdigit():
                                seven_day_avg = int(avg_text)
                    
                    # 데이터 검증 - 모든 값이 0인 경우 제외
                    if players_online == 0 and cash_players == 0 and peak_24h == 0:
                        continue
                    
                    # 사이트명 정규화
                    site_name = re.sub(r'[^\w\s\-\(\)\.&]', '', site_name).strip()
                    
                    # GG 포커 여부 확인
                    category = 'GG_POKER' if site_name in self.gg_poker_sites else 'COMPETITOR'
                    
                    site_data = {
                        'site_name': site_name,
                        'category': category,
                        'players_online': players_online,
                        'cash_players': cash_players,
                        'peak_24h': peak_24h,
                        'seven_day_avg': seven_day_avg,
                        'collected_at': datetime.now().isoformat()
                    }
                    
                    collected_data.append(site_data)
                    
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
    
    def analyze_results(self, data):
        """크롤링 결과 분석"""
        if not data:
            logger.error("분석할 데이터가 없습니다")
            return
        
        logger.info("\n" + "="*60)
        logger.info("크롤링 결과 분석")
        logger.info("="*60)
        
        # 기본 통계
        total_sites = len(data)
        gg_sites = [site for site in data if site['category'] == 'GG_POKER']
        competitor_sites = [site for site in data if site['category'] == 'COMPETITOR']
        
        # 총 플레이어 수 계산
        total_players = sum(site['players_online'] for site in data)
        total_cash = sum(site['cash_players'] for site in data)
        
        logger.info(f"총 사이트 수: {total_sites}개")
        logger.info(f"GG 포커 사이트: {len(gg_sites)}개")
        logger.info(f"경쟁사 사이트: {len(competitor_sites)}개")
        logger.info(f"총 온라인 플레이어: {total_players:,}명")
        logger.info(f"총 캐시 플레이어: {total_cash:,}명")
        
        # GG 포커 상세 정보
        if gg_sites:
            logger.info("GG 포커 사이트 상세:")
            for site in gg_sites:
                logger.info(f"   • {site['site_name']}: {site['players_online']:,}명 온라인")
        
        # 상위 10개 사이트
        logger.info(f"\n상위 10개 사이트 (플레이어 수 기준):")
        sorted_sites = sorted(data, key=lambda x: x['players_online'], reverse=True)
        
        for i, site in enumerate(sorted_sites[:10]):
            category_icon = "" if site['category'] == 'GG_POKER' else ""
            logger.info(f"{i+1:2d}. {category_icon} {site['site_name']:25s}: {site['players_online']:8,}명")
        
        # 데이터 저장
        result = {
            'crawl_time': datetime.now().isoformat(),
            'total_sites': total_sites,
            'gg_poker_sites': len(gg_sites),
            'competitor_sites': len(competitor_sites),
            'total_players': total_players,
            'total_cash_players': total_cash,
            'sites': data
        }
        
        # JSON 파일로 저장
        filename = f"live_crawling_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n💾 결과가 {filename}에 저장되었습니다!")
        
        return result

