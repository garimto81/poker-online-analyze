#!/usr/bin/env python3
"""
Firebase Realtime Database 업로더
GitHub Pages와 호환되도록 데이터를 Realtime Database에 업로드
"""
import json
import requests
from datetime import datetime, timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Firebase Realtime Database URL
FIREBASE_DB_URL = "https://poker-analyzer-ggp.firebaseio.com"

def upload_to_realtime_database(data):
    """Realtime Database에 데이터 업로드"""
    if not data:
        logger.warning("업로드할 데이터가 없습니다.")
        return False
    
    try:
        # 현재 날짜를 키로 사용
        date_key = datetime.now().strftime("%Y-%m-%d")
        
        # 데이터 구조 생성
        db_data = {
            "date": date_key,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "sites": []
        }
        
        # 사이트 데이터 변환
        for site in data:
            site_data = {
                "siteName": site.get('site_name', ''),
                "category": site.get('category', 'COMPETITOR'),
                "rank": site.get('rank', 999),
                "cashPlayers": site.get('cash_players', 0),
                "playersOnline": site.get('players_online', 0),
                "peak24h": site.get('peak_24h', 0),
                "sevenDayAvg": site.get('seven_day_avg', 0)
            }
            db_data["sites"].append(site_data)
        
        # 전체 통계 추가
        total_cash = sum(s.get('cash_players', 0) for s in data)
        total_online = sum(s.get('players_online', 0) for s in data)
        gg_sites = [s for s in data if s.get('category') == 'GG_POKER']
        gg_total = sum(s.get('cash_players', 0) for s in gg_sites)
        
        db_data["summary"] = {
            "totalSites": len(data),
            "totalCashPlayers": total_cash,
            "totalOnlinePlayers": total_online,
            "ggNetworkSites": len(gg_sites),
            "ggNetworkPlayers": gg_total,
            "ggNetworkShare": round((gg_total / total_cash * 100) if total_cash > 0 else 0, 1)
        }
        
        # Realtime Database에 업로드
        # 1. pokerData/{date} 경로에 저장
        url = f"{FIREBASE_DB_URL}/pokerData/{date_key}.json"
        response = requests.put(url, json=db_data)
        
        if response.status_code == 200:
            logger.info(f"✅ Realtime Database 업로드 성공: {date_key}")
            
            # 2. latest 경로에도 저장 (최신 데이터 빠른 접근용)
            latest_url = f"{FIREBASE_DB_URL}/latest.json"
            requests.put(latest_url, json=db_data)
            
            return True
        else:
            logger.error(f"❌ Realtime Database 업로드 실패: {response.status_code}")
            logger.error(response.text)
            return False
            
    except Exception as e:
        logger.error(f"Realtime Database 업로드 중 오류: {e}")
        return False

def migrate_firestore_to_realtime():
    """Firestore 데이터를 Realtime Database로 마이그레이션"""
    try:
        # 최근 7일 데이터 가져오기 (예시)
        logger.info("Firestore to Realtime Database 마이그레이션 시작...")
        
        # 여기에 Firestore에서 데이터를 가져오는 로직 추가
        # ...
        
        logger.info("마이그레이션 완료")
        
    except Exception as e:
        logger.error(f"마이그레이션 실패: {e}")

if __name__ == "__main__":
    # 테스트 데이터
    test_data = [
        {
            'site_name': 'WPT Global',
            'category': 'WPT',
            'rank': 1,
            'players_online': 5219,
            'cash_players': 1694,
            'peak_24h': 3825,
            'seven_day_avg': 2400
        },
        {
            'site_name': 'GGPoker ON',
            'category': 'GG_POKER',
            'rank': 7,
            'players_online': 2737,
            'cash_players': 532,
            'peak_24h': 679,
            'seven_day_avg': 375
        }
    ]
    
    # 업로드 테스트
    upload_to_realtime_database(test_data)