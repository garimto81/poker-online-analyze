#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PokerScout 실시간 크롤링 실행 및 결과 표시
online_data_collector.py와 동일한 로직으로 전체 사이트 크롤링
+ Firebase Firestore 연동 기능 추가 (효율적인 구조)
"""

import cloudscraper
from bs4 import BeautifulSoup
import json
from datetime import datetime, timezone
import logging
import sys
import re
import os

import firebase_admin
from firebase_admin import credentials, firestore

# Firebase Admin SDK 초기화
try:
    # GitHub Actions 환경과 로컬 환경 모두 지원
    possible_key_paths = [
        # GitHub Actions 환경
        os.path.join(os.path.dirname(__file__), '..', '..', 'key', 'firebase-service-account-key.json'),
        # 로컬 환경 (backend 폴더 기준)
        os.path.join(os.path.dirname(__file__), '..', '..', '..', 'key', 'firebase-service-account-key.json'),
        # 환경 변수로 지정된 경로
        os.environ.get('FIREBASE_KEY_PATH', '')
    ]
    
    key_path = None
    for path in possible_key_paths:
        if path and os.path.exists(path):
            key_path = os.path.abspath(path)
            break
    
    if not key_path:
        raise FileNotFoundError("Firebase 서비스 계정 키 파일을 찾을 수 없습니다.")
    
    cred = credentials.Certificate(key_path)
    if not firebase_admin._apps:
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    logger = logging.getLogger(__name__)
    logger.info(f"Firebase Admin SDK가 성공적으로 초기화되었습니다. (키 파일: {key_path})")
except Exception as e:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.error(f"Firebase Admin SDK 초기화 실패: {e}")
    db = None

# 로깅 설정 (Firebase 초기화 후 설정 보장)
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def upload_to_firestore_efficiently(data):
    """
    수집된 데이터를 효율적인 구조로 Firestore에 업로드합니다.
    - `sites` 컬렉션: 사이트의 고정 정보 저장 (중복 방지)
    - `traffic_logs` 하위 컬렉션: 시간에 따른 트래픽 데이터 저장
    """
    if not db:
        logger.error("Firestore 클라이언트가 초기화되지 않아 업로드할 수 없습니다.")
        return

    if not data:
        logger.warning("업로드할 데이터가 없습니다.")
        return

    logger.info("효율적인 구조로 Firestore에 데이터 업로드 시작...")
    
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
            'last_updated_at': firestore.SERVER_TIMESTAMP # 서버 시간으로 업데이트
        }
        # set(..., merge=True)를 사용하여 기존 문서는 업데이트, 없는 문서는 생성
        batch.set(site_ref, site_info, merge=True)

        # 2. `traffic_logs` 하위 컬렉션 처리
        log_ref = site_ref.collection('traffic_logs').document(collected_at_iso)
        traffic_data = {
            'players_online': site_data['players_online'],
            'cash_players': site_data['cash_players'],
            'peak_24h': site_data['peak_24h'],
            'seven_day_avg': site_data['seven_day_avg'],
            # ISO 8601 문자열을 Firestore 타임스탬프 객체로 변환
            'collected_at': datetime.fromisoformat(collected_at_iso).replace(tzinfo=timezone.utc)
        }
        batch.set(log_ref, traffic_data)

    try:
        # Batch 작업 일괄 커밋
        batch.commit()
        logger.info(f"성공적으로 {len(data)}개 사이트의 데이터를 효율적인 구조로 Firestore에 업로드했습니다.")
    except Exception as e:
        logger.error(f"Firestore Batch 업로드 중 오류 발생: {e}")
        import traceback
        logger.error(traceback.format_exc())

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
    
    def analyze_and_save(self, data):
        if not data:
            logger.error("분석할 데이터가 없습니다")
            return
        
        logger.info("\n" + "="*60)
        logger.info("크롤링 결과 분석")
        logger.info("="*60)
        
        total_sites = len(data)
        total_players = sum(site['players_online'] for site in data)
        logger.info(f"총 사이트 수: {total_sites}개, 총 온라인 플레이어: {total_players:,}명")
        
        # 로컬 JSON 파일 저장 (백업 및 디버깅용)
        filename = f"live_crawling_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"💾 결과가 로컬 백업 파일({filename})에 저장되었습니다!")
        
        # GitHub JSON 백업 파일 생성 (data 폴더에 저장)
        self.create_github_backup(data, filename)
        
        # 효율적인 구조로 Firestore에 업로드
        upload_to_firestore_efficiently(data)
        
        return data
    
    def create_github_backup(self, data, filename):
        """
        GitHub Actions 환경에서 data 폴더에 JSON 백업 파일을 생성합니다.
        """
        try:
            # data 디렉토리 생성 (없는 경우)
            data_dir = os.path.join(os.getcwd(), 'data')
            os.makedirs(data_dir, exist_ok=True)
            
            # GitHub 백업 파일 경로
            github_backup_path = os.path.join(data_dir, filename)
            
            # JSON 파일 저장
            with open(github_backup_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"🔄 GitHub 백업 파일이 생성되었습니다: {github_backup_path}")
            
            # 파일 크기와 요약 정보 로깅
            file_size = os.path.getsize(github_backup_path)
            logger.info(f"📁 백업 파일 크기: {file_size:,} bytes")
            logger.info(f"📊 백업된 데이터: {len(data)}개 사이트, {sum(site['players_online'] for site in data):,}명 플레이어")
            
        except Exception as e:
            logger.error(f"GitHub 백업 파일 생성 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == '__main__':
    crawler = LivePokerScoutCrawler()
    crawled_data = crawler.crawl_pokerscout_data()
    if crawled_data:
        crawler.analyze_and_save(crawled_data)
