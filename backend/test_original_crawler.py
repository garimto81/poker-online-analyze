#!/usr/bin/env python3
"""
기존 크롤러 테스트 스크립트
"""
import sys
import os
import logging
from datetime import datetime

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_original_crawler():
    """기존 cloudscraper 기반 크롤러 테스트"""
    logger.info("=" * 50)
    logger.info("기존 크롤러 (cloudscraper) 테스트 시작")
    logger.info("=" * 50)
    
    try:
        from github_actions_crawler_firestore import LivePokerScoutCrawler
        
        logger.info("LivePokerScoutCrawler 인스턴스 생성...")
        crawler = LivePokerScoutCrawler()
        
        logger.info("PokerScout.com 크롤링 시도...")
        data = crawler.crawl_pokerscout_data()
        
        if data:
            logger.info(f"✅ 크롤링 성공: {len(data)}개 사이트 발견")
            
            # 상위 10개 사이트 정보 출력
            logger.info("\n📊 상위 10개 사이트 데이터:")
            logger.info("-" * 60)
            for i, site in enumerate(data[:10], 1):
                logger.info(
                    f"{i:2}. {site['site_name']:20} | "
                    f"온라인: {site['players_online']:6} | "
                    f"캐시: {site['cash_players']:6} | "
                    f"피크: {site['peak_24h']:6}"
                )
            
            # 통계 정보
            total_players = sum(site['players_online'] for site in data)
            total_cash = sum(site['cash_players'] for site in data)
            gg_sites = [s for s in data if s['category'] == 'GG_POKER']
            
            logger.info("\n📈 전체 통계:")
            logger.info(f"- 총 사이트 수: {len(data)}개")
            logger.info(f"- 전체 온라인 플레이어: {total_players:,}명")
            logger.info(f"- 전체 캐시 플레이어: {total_cash:,}명")
            logger.info(f"- GG 네트워크 사이트: {len(gg_sites)}개")
            
            return True, data
        else:
            logger.error("❌ 크롤링 실패: 데이터를 가져오지 못함")
            logger.error("PokerScout.com이 크롤링을 차단하고 있을 가능성이 높습니다.")
            return False, None
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False, None

def main():
    """메인 실행 함수"""
    logger.info("🔍 기존 크롤러 상세 테스트")
    logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"현재 디렉토리: {os.getcwd()}")
    
    success, data = test_original_crawler()
    
    if success:
        logger.info("\n✅ 결론: 기존 크롤러가 정상 작동합니다!")
        logger.info("PokerScout.com 접근이 가능합니다.")
    else:
        logger.info("\n❌ 결론: 기존 크롤러로도 접근 불가")
        logger.info("PokerScout.com이 크롤링을 차단 중입니다.")
        logger.info("\n💡 해결 방안:")
        logger.info("1. Selenium + 올바른 ChromeDriver 버전 사용")
        logger.info("2. 프록시 서버 활용")
        logger.info("3. User-Agent 및 헤더 수정")
        logger.info("4. 요청 간격 증가")

if __name__ == "__main__":
    main()