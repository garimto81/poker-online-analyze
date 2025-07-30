import logging
import sys
import os
from datetime import datetime, timezone
import requests
import time

# Setup logging
log_dir = os.path.join(os.path.dirname(__file__), 'logs')
os.makedirs(log_dir, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join(log_dir, f'crawler_{datetime.now().strftime("%Y%m%d")}.log')),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

def run_scheduled_crawl():
    """매일 실행되는 크롤링 작업"""
    logger.info("=== 스케줄된 크롤링 시작 ===")
    
    try:
        # 백엔드 서버가 실행 중인지 확인
        max_retries = 3
        retry_delay = 10
        
        for attempt in range(max_retries):
            try:
                # 서버 상태 확인
                response = requests.get('http://localhost:4001/')
                if response.status_code == 200:
                    logger.info("백엔드 서버가 정상 작동 중입니다.")
                    break
            except requests.exceptions.ConnectionError:
                logger.warning(f"백엔드 서버 연결 실패 (시도 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    logger.info(f"{retry_delay}초 후 재시도...")
                    time.sleep(retry_delay)
                else:
                    logger.error("백엔드 서버에 연결할 수 없습니다. 크롤링을 중단합니다.")
                    return False
        
        # 크롤링 API 호출
        logger.info("크롤링 API 호출 중...")
        crawl_response = requests.post(
            'http://localhost:4001/api/firebase/crawl_and_save_data/',
            timeout=300  # 5분 타임아웃
        )
        
        if crawl_response.status_code == 200:
            result = crawl_response.json()
            logger.info(f"크롤링 성공: {result.get('count', 0)}개 사이트 데이터 수집")
            logger.info(f"타임스탬프: {result.get('timestamp', 'N/A')}")
            
            # 수집된 데이터 요약 정보 가져오기
            try:
                ranking_response = requests.get('http://localhost:4001/api/firebase/current_ranking/')
                if ranking_response.status_code == 200:
                    ranking_data = ranking_response.json()
                    total_players = sum(site['players_online'] for site in ranking_data)
                    logger.info(f"현재 총 온라인 플레이어 수: {total_players:,}")
                    logger.info(f"상위 3개 사이트:")
                    for i, site in enumerate(ranking_data[:3]):
                        logger.info(f"  {i+1}. {site['site_name']}: {site['players_online']:,} players")
            except Exception as e:
                logger.warning(f"순위 정보 조회 실패: {e}")
            
            return True
        else:
            logger.error(f"크롤링 API 호출 실패: {crawl_response.status_code}")
            logger.error(f"응답: {crawl_response.text}")
            return False
            
    except Exception as e:
        logger.error(f"예상치 못한 오류 발생: {e}", exc_info=True)
        return False
    finally:
        logger.info("=== 스케줄된 크롤링 종료 ===\n")

if __name__ == "__main__":
    # 직접 실행 시
    success = run_scheduled_crawl()
    sys.exit(0 if success else 1)