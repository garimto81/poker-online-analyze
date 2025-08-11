#!/usr/bin/env python3
"""
Selenium 크롤러 로컬 테스트 스크립트
- 다양한 설정으로 크롤러 테스트
- 성공/실패 케이스 확인
"""
import sys
import os
import logging
from datetime import datetime
import json

# 경로 설정
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_basic_crawling():
    """기본 크롤링 테스트"""
    logger.info("=" * 50)
    logger.info("테스트 1: 기본 크롤링 (프록시 없음, 헤드리스)")
    logger.info("=" * 50)
    
    try:
        from selenium_crawler_advanced import EnhancedPokerScoutCrawler
        
        crawler = EnhancedPokerScoutCrawler(use_proxy=False, headless=True)
        data = crawler.crawl_pokerscout_data()
        
        if data:
            logger.info(f"✅ 성공: {len(data)}개 사이트 크롤링")
            # 상위 5개 사이트 출력
            for i, site in enumerate(data[:5], 1):
                logger.info(f"  {i}. {site['site_name']}: {site['players_online']} players")
            return True
        else:
            logger.error("❌ 실패: 데이터를 가져오지 못함")
            return False
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_with_proxy():
    """프록시를 사용한 크롤링 테스트"""
    logger.info("=" * 50)
    logger.info("테스트 2: 프록시 로테이션 크롤링")
    logger.info("=" * 50)
    
    try:
        from selenium_crawler_advanced import EnhancedPokerScoutCrawler
        
        crawler = EnhancedPokerScoutCrawler(use_proxy=True, headless=True)
        data = crawler.crawl_with_retry()
        
        if data:
            logger.info(f"✅ 성공: {len(data)}개 사이트 크롤링 (프록시 사용)")
            return True
        else:
            logger.warning("⚠️ 프록시로 실패, 일반 모드로 재시도...")
            crawler = EnhancedPokerScoutCrawler(use_proxy=False, headless=True)
            data = crawler.crawl_pokerscout_data()
            if data:
                logger.info(f"✅ 일반 모드로 성공: {len(data)}개 사이트")
                return True
            else:
                logger.error("❌ 모든 방법 실패")
                return False
                
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        return False

def test_visible_browser():
    """브라우저를 보이게 하여 테스트 (디버깅용)"""
    logger.info("=" * 50)
    logger.info("테스트 3: 브라우저 표시 모드 (디버깅)")
    logger.info("=" * 50)
    
    try:
        from selenium_crawler_advanced import EnhancedPokerScoutCrawler
        
        logger.info("브라우저가 열립니다. 크롤링 과정을 확인하세요...")
        crawler = EnhancedPokerScoutCrawler(use_proxy=False, headless=False)
        data = crawler.crawl_pokerscout_data()
        
        if data:
            logger.info(f"✅ 성공: {len(data)}개 사이트 크롤링")
            return True
        else:
            logger.error("❌ 실패: 데이터를 가져오지 못함")
            return False
            
    except Exception as e:
        logger.error(f"❌ 테스트 실패: {e}")
        return False

def test_old_crawler():
    """기존 크롤러와 비교 테스트"""
    logger.info("=" * 50)
    logger.info("테스트 4: 기존 크롤러 (cloudscraper) 테스트")
    logger.info("=" * 50)
    
    try:
        from github_actions_crawler_firestore import LivePokerScoutCrawler
        
        crawler = LivePokerScoutCrawler()
        data = crawler.crawl_pokerscout_data()
        
        if data:
            logger.info(f"✅ 기존 크롤러 성공: {len(data)}개 사이트")
            return True
        else:
            logger.error("❌ 기존 크롤러도 실패 (PokerScout가 차단 중)")
            return False
            
    except Exception as e:
        logger.error(f"❌ 기존 크롤러 테스트 실패: {e}")
        return False

def save_test_results(results):
    """테스트 결과 저장"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"test_results_{timestamp}.json"
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    logger.info(f"테스트 결과를 {filename}에 저장했습니다.")

def main():
    """메인 테스트 실행"""
    logger.info("🚀 Selenium 크롤러 테스트 시작")
    logger.info("현재 디렉토리: " + os.getcwd())
    
    results = {
        'test_time': datetime.now().isoformat(),
        'tests': {}
    }
    
    # 필수 라이브러리 확인
    try:
        import undetected_chromedriver
        import selenium
        logger.info("✅ 필수 라이브러리 설치 확인됨")
    except ImportError:
        logger.error("❌ 필수 라이브러리가 설치되지 않았습니다.")
        logger.error("다음 명령어를 실행하세요:")
        logger.error("pip install undetected-chromedriver selenium")
        return
    
    # 테스트 실행
    tests = [
        ("기본 크롤링", test_basic_crawling),
        ("프록시 크롤링", test_with_proxy),
        ("기존 크롤러", test_old_crawler),
    ]
    
    # 대화형 모드 확인
    if len(sys.argv) > 1 and sys.argv[1] == '--visible':
        tests.append(("브라우저 표시", test_visible_browser))
    
    for test_name, test_func in tests:
        try:
            logger.info(f"\n실행 중: {test_name}")
            success = test_func()
            results['tests'][test_name] = {
                'success': success,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"테스트 {test_name} 실행 실패: {e}")
            results['tests'][test_name] = {
                'success': False,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    # 결과 요약
    logger.info("\n" + "=" * 50)
    logger.info("📊 테스트 결과 요약")
    logger.info("=" * 50)
    
    success_count = sum(1 for r in results['tests'].values() if r.get('success'))
    total_count = len(results['tests'])
    
    for test_name, result in results['tests'].items():
        status = "✅ 성공" if result.get('success') else "❌ 실패"
        logger.info(f"{test_name}: {status}")
    
    logger.info(f"\n전체: {success_count}/{total_count} 성공")
    
    # 결과 저장
    save_test_results(results)
    
    # 권장사항
    if success_count == 0:
        logger.error("\n⚠️ 모든 테스트 실패!")
        logger.error("권장사항:")
        logger.error("1. Chrome/Chromium이 설치되어 있는지 확인")
        logger.error("2. PokerScout.com이 접속 가능한지 확인")
        logger.error("3. 방화벽/안티바이러스 설정 확인")
    elif success_count < total_count:
        logger.warning("\n⚠️ 일부 테스트만 성공")
        logger.warning("Selenium 크롤러가 작동하면 GitHub Actions에 배포 가능합니다.")
    else:
        logger.info("\n🎉 모든 테스트 성공!")
        logger.info("GitHub Actions에 배포할 준비가 완료되었습니다.")

if __name__ == "__main__":
    main()