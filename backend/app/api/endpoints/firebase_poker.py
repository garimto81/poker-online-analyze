from fastapi import APIRouter, HTTPException, Header
from typing import List, Optional
from datetime import datetime, timezone, timedelta
import firebase_admin
from firebase_admin import credentials, firestore
from ...services.poker_crawler import LivePokerScoutCrawler, upload_to_firestore_efficiently
import os
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

# Firebase 초기화 (이미 poker_crawler.py에서 초기화되었을 수 있음)
def get_firestore_client():
    try:
        # 이미 초기화되었는지 확인
        if firebase_admin._apps:
            return firestore.client()
        
        # 초기화되지 않았다면 초기화
        possible_key_paths = [
            os.path.join(os.path.dirname(__file__), '..', '..', 'key', 'firebase-service-account-key.json'),
            os.path.join(os.path.dirname(__file__), '..', '..', '..', 'key', 'firebase-service-account-key.json'),
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
        firebase_admin.initialize_app(cred)
        return firestore.client()
    except Exception as e:
        logger.error(f"Firestore 클라이언트 초기화 실패: {e}")
        raise HTTPException(status_code=500, detail="Firebase 초기화 실패")

@router.post("/crawl_and_save_data/")
async def crawl_and_save_data(x_api_key: Optional[str] = Header(None)):
    """PokerScout 데이터를 크롤링하고 Firebase에 저장합니다."""
    # API 키 검증 (프로덕션에서는 환경 변수 사용)
    import os
    expected_api_key = os.environ.get('CRAWL_API_KEY', 'default-dev-key-12345')
    
    # API 키가 제공되었고 일치하지 않으면 거부
    if x_api_key and x_api_key != expected_api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    
    try:
        crawler = LivePokerScoutCrawler()
        crawled_data = crawler.crawl_pokerscout_data()
        
        if not crawled_data:
            raise HTTPException(status_code=500, detail="PokerScout에서 데이터를 가져오는데 실패했습니다.")
        
        # Firebase에 데이터 업로드
        upload_to_firestore_efficiently(crawled_data)
        
        return {
            "message": "데이터가 성공적으로 크롤링되고 저장되었습니다!",
            "count": len(crawled_data),
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"크롤링 및 저장 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sites/")
async def get_sites():
    """모든 사이트 정보를 가져옵니다."""
    try:
        db = get_firestore_client()
        sites_ref = db.collection('sites')
        sites = []
        
        for doc in sites_ref.stream():
            site_data = doc.to_dict()
            site_data['id'] = doc.id
            sites.append(site_data)
        
        return sites
    except Exception as e:
        logger.error(f"사이트 목록 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sites/{site_name}/latest/")
async def get_site_latest_stats(site_name: str):
    """특정 사이트의 최신 통계를 가져옵니다."""
    try:
        db = get_firestore_client()
        site_ref = db.collection('sites').document(site_name)
        
        # 사이트 정보 가져오기
        site_doc = site_ref.get()
        if not site_doc.exists:
            raise HTTPException(status_code=404, detail=f"사이트를 찾을 수 없습니다: {site_name}")
        
        site_data = site_doc.to_dict()
        site_data['id'] = site_doc.id
        
        # 최신 트래픽 로그 가져오기
        traffic_logs = site_ref.collection('traffic_logs').order_by('collected_at', direction=firestore.Query.DESCENDING).limit(1).stream()
        
        latest_log = None
        for log in traffic_logs:
            latest_log = log.to_dict()
            latest_log['id'] = log.id
            break
        
        return {
            "site": site_data,
            "latest_stats": latest_log
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"최신 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sites/{site_name}/stats/")
async def get_site_stats(site_name: str, days: int = 7):
    """특정 사이트의 통계 이력을 가져옵니다."""
    try:
        db = get_firestore_client()
        site_ref = db.collection('sites').document(site_name)
        
        # 사이트 존재 확인
        if not site_ref.get().exists:
            raise HTTPException(status_code=404, detail=f"사이트를 찾을 수 없습니다: {site_name}")
        
        # 지정된 일수만큼의 데이터 가져오기
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        
        traffic_logs = site_ref.collection('traffic_logs').where('collected_at', '>=', cutoff_date).order_by('collected_at').stream()
        
        stats = []
        for log in traffic_logs:
            log_data = log.to_dict()
            log_data['id'] = log.id
            stats.append(log_data)
        
        return {
            "site_name": site_name,
            "days": days,
            "stats": stats,
            "count": len(stats)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"통계 이력 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top10_daily_stats/")
async def get_top10_daily_stats(days: int = 7):
    """상위 10개 사이트의 일간 통계를 가져옵니다."""
    try:
        db = get_firestore_client()
        
        # 먼저 현재 순위를 가져와서 상위 10개 사이트 확인
        current_ranking = []
        sites_ref = db.collection('sites')
        
        for site_doc in sites_ref.stream():
            site_data = site_doc.to_dict()
            site_name = site_doc.id
            
            # 최신 트래픽 로그 가져오기
            traffic_logs = site_doc.reference.collection('traffic_logs').order_by('collected_at', direction=firestore.Query.DESCENDING).limit(1).stream()
            
            for log in traffic_logs:
                log_data = log.to_dict()
                current_ranking.append({
                    "site_name": site_name,
                    "players_online": log_data.get('players_online', 0),
                    "cash_players": log_data.get('cash_players', 0),
                    "peak_24h": log_data.get('peak_24h', 0),
                    "seven_day_avg": log_data.get('seven_day_avg', 0)
                })
                break
        
        # 온라인 플레이어 수로 정렬하여 상위 10개 선택
        current_ranking.sort(key=lambda x: x['players_online'], reverse=True)
        top10_sites = current_ranking[:10]
        
        # 전체 플레이어 수 계산 (점유율 계산용)
        total_players = sum(site['players_online'] for site in current_ranking)
        
        # 먼저 각 날짜별 전체 플레이어 수 계산
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        daily_totals = {}
        
        # 모든 사이트의 일별 데이터 수집
        for site_doc in sites_ref.stream():
            site_ref = site_doc.reference
            traffic_logs = site_ref.collection('traffic_logs').where('collected_at', '>=', cutoff_date).stream()
            
            for log in traffic_logs:
                log_data = log.to_dict()
                date_str = log_data['collected_at'].strftime('%Y-%m-%d')
                if date_str not in daily_totals:
                    daily_totals[date_str] = 0
                daily_totals[date_str] += log_data.get('players_online', 0)
        
        # 각 사이트의 일간 데이터 가져오기
        daily_stats = {}
        
        for site in top10_sites:
            site_name = site['site_name']
            site_ref = db.collection('sites').document(site_name)
            
            # 지난 n일간의 데이터
            traffic_logs = site_ref.collection('traffic_logs').where('collected_at', '>=', cutoff_date).order_by('collected_at').stream()
            
            daily_data = []
            for log in traffic_logs:
                log_data = log.to_dict()
                date_str = log_data['collected_at'].strftime('%Y-%m-%d')
                players_online = log_data.get('players_online', 0)
                
                # 해당 날짜의 점유율 계산
                daily_total = daily_totals.get(date_str, 0)
                daily_market_share = round((players_online / daily_total) * 100, 2) if daily_total > 0 else 0
                
                daily_data.append({
                    'date': log_data['collected_at'].isoformat(),
                    'players_online': players_online,
                    'cash_players': log_data.get('cash_players', 0),
                    'peak_24h': log_data.get('peak_24h', 0),
                    'seven_day_avg': log_data.get('seven_day_avg', 0),
                    'market_share': daily_market_share
                })
            
            # 현재 시점 점유율 계산
            market_share = (site['players_online'] / total_players * 100) if total_players > 0 else 0
            
            daily_stats[site_name] = {
                'current_stats': site,
                'market_share': round(market_share, 2),
                'daily_data': daily_data
            }
        
        return {
            'top10_sites': list(daily_stats.keys()),
            'total_players_online': total_players,
            'data': daily_stats,
            'days': days
        }
        
    except Exception as e:
        logger.error(f"상위 10개 사이트 일간 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/top10_by_category/")
async def get_top10_by_category(days: int = 7):
    """각 카테고리별 상위 10개 사이트의 일간 통계를 가져옵니다."""
    try:
        db = get_firestore_client()
        
        # 먼저 현재 순위를 가져와서 각 카테고리별 상위 10개 사이트 확인
        current_ranking = []
        sites_ref = db.collection('sites')
        
        for site_doc in sites_ref.stream():
            site_data = site_doc.to_dict()
            site_name = site_doc.id
            
            # 최신 트래픽 로그 가져오기
            traffic_logs = site_doc.reference.collection('traffic_logs').order_by('collected_at', direction=firestore.Query.DESCENDING).limit(1).stream()
            
            for log in traffic_logs:
                log_data = log.to_dict()
                current_ranking.append({
                    "site_name": site_name,
                    "players_online": log_data.get('players_online', 0),
                    "cash_players": log_data.get('cash_players', 0),
                    "peak_24h": log_data.get('peak_24h', 0),
                    "seven_day_avg": log_data.get('seven_day_avg', 0)
                })
                break
        
        # 각 카테고리별로 정렬하여 상위 10개 선택
        categories = {
            'players_online': sorted(current_ranking, key=lambda x: x['players_online'], reverse=True)[:10],
            'cash_players': sorted(current_ranking, key=lambda x: x['cash_players'], reverse=True)[:10],
            'peak_24h': sorted(current_ranking, key=lambda x: x['peak_24h'], reverse=True)[:10],
            'seven_day_avg': sorted(current_ranking, key=lambda x: x['seven_day_avg'], reverse=True)[:10]
        }
        
        # 각 카테고리별 전체 합계 계산
        totals = {
            'players_online': sum(site['players_online'] for site in current_ranking),
            'cash_players': sum(site['cash_players'] for site in current_ranking),
            'peak_24h': sum(site['peak_24h'] for site in current_ranking),
            'seven_day_avg': sum(site['seven_day_avg'] for site in current_ranking)
        }
        
        # 먼저 각 날짜별 전체 플레이어 수 계산
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        daily_totals = {}
        
        # 모든 사이트의 일별 데이터 수집
        for site_doc in sites_ref.stream():
            site_ref = site_doc.reference
            traffic_logs = site_ref.collection('traffic_logs').where('collected_at', '>=', cutoff_date).stream()
            
            for log in traffic_logs:
                log_data = log.to_dict()
                date_str = log_data['collected_at'].strftime('%Y-%m-%d')
                if date_str not in daily_totals:
                    daily_totals[date_str] = {
                        'players_online': 0,
                        'cash_players': 0,
                        'peak_24h': 0,
                        'seven_day_avg': 0
                    }
                daily_totals[date_str]['players_online'] += log_data.get('players_online', 0)
                daily_totals[date_str]['cash_players'] += log_data.get('cash_players', 0)
                daily_totals[date_str]['peak_24h'] += log_data.get('peak_24h', 0)
                daily_totals[date_str]['seven_day_avg'] += log_data.get('seven_day_avg', 0)
        
        # 각 카테고리별 결과 구성
        result = {}
        
        for category, top10_sites in categories.items():
            category_data = {}
            
            for site in top10_sites:
                site_name = site['site_name']
                site_ref = db.collection('sites').document(site_name)
                
                # 지난 n일간의 데이터
                traffic_logs = site_ref.collection('traffic_logs').where('collected_at', '>=', cutoff_date).order_by('collected_at').stream()
                
                daily_data = []
                for log in traffic_logs:
                    log_data = log.to_dict()
                    date_str = log_data['collected_at'].strftime('%Y-%m-%d')
                    
                    # 해당 카테고리의 값과 점유율 계산
                    value = log_data.get(category, 0)
                    daily_total = daily_totals.get(date_str, {}).get(category, 0)
                    daily_market_share = round((value / daily_total) * 100, 2) if daily_total > 0 else 0
                    
                    daily_data.append({
                        'date': log_data['collected_at'].isoformat(),
                        'value': value,
                        'market_share': daily_market_share,
                        'players_online': log_data.get('players_online', 0),
                        'cash_players': log_data.get('cash_players', 0),
                        'peak_24h': log_data.get('peak_24h', 0),
                        'seven_day_avg': log_data.get('seven_day_avg', 0)
                    })
                
                # 현재 시점 점유율 계산
                current_value = site[category]
                market_share = (current_value / totals[category] * 100) if totals[category] > 0 else 0
                
                category_data[site_name] = {
                    'current_stats': site,
                    'market_share': round(market_share, 2),
                    'daily_data': daily_data
                }
            
            result[category] = {
                'top10_sites': [site['site_name'] for site in top10_sites],
                'total': totals[category],
                'data': category_data
            }
        
        return {
            'categories': result,
            'days': days
        }
        
    except Exception as e:
        logger.error(f"카테고리별 상위 10개 사이트 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/current_ranking/")
async def get_current_ranking():
    """현재 시점의 사이트 순위를 가져옵니다."""
    try:
        db = get_firestore_client()
        sites_ref = db.collection('sites')
        
        ranking = []
        
        for site_doc in sites_ref.stream():
            site_data = site_doc.to_dict()
            site_name = site_doc.id
            
            # 최신 트래픽 로그 가져오기
            traffic_logs = site_doc.reference.collection('traffic_logs').order_by('collected_at', direction=firestore.Query.DESCENDING).limit(1).stream()
            
            for log in traffic_logs:
                log_data = log.to_dict()
                ranking.append({
                    "site_name": site_name,
                    "category": site_data.get('category', 'UNKNOWN'),
                    "players_online": log_data.get('players_online', 0),
                    "cash_players": log_data.get('cash_players', 0),
                    "peak_24h": log_data.get('peak_24h', 0),
                    "seven_day_avg": log_data.get('seven_day_avg', 0),
                    "last_updated": log_data.get('collected_at')
                })
                break
        
        # 온라인 플레이어 수로 정렬
        ranking.sort(key=lambda x: x['players_online'], reverse=True)
        
        # 순위 추가
        for i, site in enumerate(ranking):
            site['rank'] = i + 1
        
        return ranking
    except Exception as e:
        logger.error(f"현재 순위 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/all_sites_daily_stats/")
async def get_all_sites_daily_stats(days: int = 7):
    """모든 사이트의 일간 통계를 가져옵니다."""
    try:
        db = get_firestore_client()
        
        # 먼저 현재 모든 사이트의 정보 가져오기
        current_ranking = []
        sites_ref = db.collection('sites')
        
        for site_doc in sites_ref.stream():
            site_data = site_doc.to_dict()
            site_name = site_doc.id
            
            # 최신 트래픽 로그 가져오기
            traffic_logs = site_doc.reference.collection('traffic_logs').order_by('collected_at', direction=firestore.Query.DESCENDING).limit(1).stream()
            
            for log in traffic_logs:
                log_data = log.to_dict()
                current_ranking.append({
                    "site_name": site_name,
                    "category": site_data.get('category', 'UNKNOWN'),
                    "players_online": log_data.get('players_online', 0),
                    "cash_players": log_data.get('cash_players', 0),
                    "peak_24h": log_data.get('peak_24h', 0),
                    "seven_day_avg": log_data.get('seven_day_avg', 0)
                })
                break
        
        # 각 사이트의 일간 데이터 가져오기
        cutoff_date = datetime.now(timezone.utc) - timedelta(days=days)
        all_sites_data = {}
        
        for site in current_ranking:
            site_name = site['site_name']
            site_ref = db.collection('sites').document(site_name)
            
            # 지난 n일간의 데이터
            traffic_logs = site_ref.collection('traffic_logs').where('collected_at', '>=', cutoff_date).order_by('collected_at').stream()
            
            daily_data = []
            for log in traffic_logs:
                log_data = log.to_dict()
                daily_data.append({
                    'date': log_data['collected_at'].isoformat(),
                    'players_online': log_data.get('players_online', 0),
                    'cash_players': log_data.get('cash_players', 0),
                    'peak_24h': log_data.get('peak_24h', 0),
                    'seven_day_avg': log_data.get('seven_day_avg', 0)
                })
            
            all_sites_data[site_name] = {
                'current_stats': site,
                'daily_data': daily_data
            }
        
        return {
            'total_sites': len(all_sites_data),
            'data': all_sites_data,
            'days': days
        }
        
    except Exception as e:
        logger.error(f"전체 사이트 일간 통계 조회 실패: {e}")
        raise HTTPException(status_code=500, detail=str(e))