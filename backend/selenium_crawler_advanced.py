#!/usr/bin/env python3
"""
향상된 Selenium 기반 PokerScout 크롤러
- undetected-chromedriver 사용으로 봇 탐지 회피
- 프록시 로테이션 지원
- 고급 에러 처리 및 재시도 로직
"""
import sys
import os
import logging
from datetime import datetime, timezone
import json
import re
import time
import random
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from google.auth.transport.requests import Request

# Selenium 관련 임포트
try:
    import undetected_chromedriver as uc
    from selenium import webdriver
    from selenium.webdriver.common.by import By
    from selenium.webdriver.support.ui import WebDriverWait
    from selenium.webdriver.support import expected_conditions as EC
    from selenium.common.exceptions import TimeoutException, WebDriverException
except ImportError:
    print("필요한 라이브러리를 설치해주세요:")
    print("pip install undetected-chromedriver selenium")
    sys.exit(1)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Firebase 프로젝트 설정
FIREBASE_PROJECT_ID = "poker-online-analyze"
FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

# 무료 프록시 리스트 (선택적)
FREE_PROXY_LIST = [
    # 실제 사용 시 유효한 프록시로 교체 필요
    # "http://proxy1.com:8080",
    # "http://proxy2.com:8080",
]

class ProxyManager:
    """프록시 로테이션 관리자"""
    def __init__(self):
        self.proxies = self._fetch_free_proxies()
        self.current_proxy_index = 0
        
    def _fetch_free_proxies(self) -> List[str]:
        """무료 프록시 리스트 가져오기 (API 또는 하드코딩)"""
        try:
            # ProxyScrape API 사용 예시 (무료)
            response = requests.get(
                'https://api.proxyscrape.com/v2/',
                params={
                    'request': 'get',
                    'protocol': 'http',
                    'timeout': '10000',
                    'country': 'all',
                    'ssl': 'all',
                    'anonymity': 'all',
                    'simplified': 'true'
                },
                timeout=10
            )
            if response.status_code == 200:
                proxy_list = response.text.strip().split('\n')
                # HTTP 형식으로 변환
                return [f"http://{proxy}" for proxy in proxy_list[:10] if proxy]
        except Exception as e:
            logger.warning(f"프록시 목록 가져오기 실패: {e}")
        
        # 프록시 가져오기 실패 시 하드코딩된 리스트 또는 빈 리스트 반환
        return FREE_PROXY_LIST if FREE_PROXY_LIST else []
    
    def get_next_proxy(self) -> Optional[str]:
        """다음 프록시 반환"""
        if not self.proxies:
            return None
        proxy = self.proxies[self.current_proxy_index % len(self.proxies)]
        self.current_proxy_index += 1
        return proxy
    
    def mark_proxy_as_bad(self, proxy: str):
        """실패한 프록시 제거"""
        if proxy in self.proxies:
            self.proxies.remove(proxy)
            logger.info(f"프록시 제거됨: {proxy}, 남은 프록시: {len(self.proxies)}개")

class EnhancedPokerScoutCrawler:
    def __init__(self, use_proxy: bool = True, headless: bool = True):
        self.use_proxy = use_proxy
        self.headless = headless
        self.proxy_manager = ProxyManager() if use_proxy else None
        self.gg_poker_sites = ['GGNetwork', 'GGPoker ON', 'GG Poker', 'GGPoker']
        self.driver = None
        self.max_retries = 3
        
    def _create_driver(self, proxy: Optional[str] = None) -> uc.Chrome:
        """Chrome 드라이버 생성 (undetected-chromedriver 사용)"""
        options = uc.ChromeOptions()
        
        # 헤드리스 모드 설정
        if self.headless:
            options.add_argument('--headless')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        
        # 추가 옵션으로 탐지 회피
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-web-security')
        options.add_argument('--disable-features=IsolateOrigins,site-per-process')
        options.add_argument(f'--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # 프록시 설정
        if proxy:
            options.add_argument(f'--proxy-server={proxy}')
            logger.info(f"프록시 사용: {proxy}")
        
        # 이미지 로딩 비활성화 (속도 향상)
        prefs = {"profile.managed_default_content_settings.images": 2}
        options.add_experimental_option("prefs", prefs)
        
        # GitHub Actions 환경 감지
        if os.environ.get('GITHUB_ACTIONS'):
            options.add_argument('--disable-gpu')
            options.add_argument('--window-size=1920,1080')
        
        try:
            driver = uc.Chrome(options=options, version_main=None)
            # 페이지 로드 타임아웃 설정
            driver.set_page_load_timeout(30)
            return driver
        except Exception as e:
            logger.error(f"드라이버 생성 실패: {e}")
            raise
    
    def _random_delay(self, min_sec: float = 0.5, max_sec: float = 2.0):
        """무작위 지연 (인간처럼 보이기)"""
        time.sleep(random.uniform(min_sec, max_sec))
    
    def _scroll_page(self, driver):
        """페이지 스크롤 (동적 콘텐츠 로딩)"""
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.3);")
        self._random_delay(0.3, 0.7)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight * 0.6);")
        self._random_delay(0.3, 0.7)
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
    def crawl_with_retry(self) -> List[Dict]:
        """재시도 로직이 포함된 크롤링"""
        for attempt in range(self.max_retries):
            proxy = None
            if self.use_proxy and self.proxy_manager:
                proxy = self.proxy_manager.get_next_proxy()
                
            try:
                logger.info(f"크롤링 시도 {attempt + 1}/{self.max_retries}")
                result = self.crawl_pokerscout_data(proxy)
                if result:
                    return result
            except Exception as e:
                logger.error(f"크롤링 실패 (시도 {attempt + 1}): {e}")
                if proxy and self.proxy_manager:
                    self.proxy_manager.mark_proxy_as_bad(proxy)
                    
        logger.error("모든 재시도 실패")
        return []
    
    def crawl_pokerscout_data(self, proxy: Optional[str] = None) -> List[Dict]:
        """PokerScout 데이터 크롤링 (Selenium 사용)"""
        logger.info("Selenium 기반 PokerScout 크롤링 시작...")
        driver = None
        
        try:
            # 드라이버 생성
            driver = self._create_driver(proxy)
            
            # PokerScout 접속
            logger.info("PokerScout.com 접속 중...")
            driver.get('https://www.pokerscout.com')
            
            # 초기 지연 (페이지 로딩 대기)
            self._random_delay(2, 4)
            
            # 페이지 스크롤 (동적 콘텐츠 로딩)
            self._scroll_page(driver)
            
            # 테이블 찾기 (여러 방법 시도)
            logger.info("랭킹 테이블 검색 중...")
            table = None
            
            # 방법 1: 클래스명으로 찾기
            try:
                wait = WebDriverWait(driver, 10)
                table = wait.until(EC.presence_of_element_located((By.CLASS_NAME, "rankTable")))
                logger.info("rankTable 클래스로 테이블 발견")
            except TimeoutException:
                logger.warning("rankTable 클래스로 테이블을 찾을 수 없음")
                
                # 방법 2: XPath로 찾기
                try:
                    table = driver.find_element(By.XPATH, "//table[contains(@class, 'rank')]")
                    logger.info("XPath로 테이블 발견")
                except:
                    # 방법 3: 모든 테이블 중 첫 번째
                    tables = driver.find_elements(By.TAG_NAME, "table")
                    if tables:
                        table = tables[0]
                        logger.info(f"첫 번째 테이블 사용 (총 {len(tables)}개 테이블 발견)")
            
            if not table:
                # 페이지 소스를 BeautifulSoup으로 파싱
                logger.info("Selenium 대신 BeautifulSoup으로 파싱 시도...")
                page_source = driver.page_source
                return self._parse_with_beautifulsoup(page_source)
            
            # 테이블 데이터 추출
            collected_data = []
            rows = table.find_elements(By.TAG_NAME, "tr")[1:]  # 헤더 제외
            logger.info(f"발견된 행 수: {len(rows)}")
            
            for i, row in enumerate(rows):
                try:
                    # 사이트 이름 추출
                    try:
                        brand_title = row.find_element(By.CLASS_NAME, "brand-title")
                        site_name = brand_title.text.strip()
                    except:
                        continue
                    
                    if not site_name or len(site_name) < 2:
                        continue
                    
                    # 플레이어 통계 추출
                    players_online = self._extract_number(row, "online")
                    cash_players = self._extract_number(row, "cash")
                    peak_24h = self._extract_number(row, "peak")
                    seven_day_avg = self._extract_number(row, "avg")
                    
                    if players_online == 0 and cash_players == 0 and peak_24h == 0:
                        continue
                    
                    # 데이터 정리
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
                    logger.debug(f"행 {i+1} 처리 중 오류: {e}")
                    continue
            
            logger.info(f"크롤링 완료: {len(collected_data)}개 사이트 수집")
            return collected_data
            
        except Exception as e:
            logger.error(f"크롤링 실패: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # 스크린샷 저장 (디버깅용)
            if driver:
                try:
                    screenshot_path = f"error_screenshot_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
                    driver.save_screenshot(screenshot_path)
                    logger.info(f"에러 스크린샷 저장: {screenshot_path}")
                except:
                    pass
            
            return []
            
        finally:
            if driver:
                try:
                    driver.quit()
                except:
                    pass
    
    def _parse_with_beautifulsoup(self, page_source: str) -> List[Dict]:
        """BeautifulSoup으로 페이지 소스 파싱"""
        try:
            soup = BeautifulSoup(page_source, 'html.parser')
            table = soup.find('table', {'class': 'rankTable'})
            
            if not table:
                # 모든 테이블 검색
                tables = soup.find_all('table')
                logger.info(f"총 {len(tables)}개 테이블 발견")
                if tables:
                    table = tables[0]
            
            if not table:
                logger.error("테이블을 찾을 수 없습니다")
                return []
            
            collected_data = []
            rows = table.find_all('tr')[1:]
            
            for row in rows:
                try:
                    brand_title = row.find('span', {'class': 'brand-title'})
                    if not brand_title:
                        continue
                    
                    site_name = brand_title.get_text(strip=True)
                    if not site_name or len(site_name) < 2:
                        continue
                    
                    # 통계 추출
                    players_online = 0
                    online_td = row.find('td', {'id': 'online'})
                    if online_td:
                        span = online_td.find('span')
                        if span:
                            text = span.get_text(strip=True).replace(',', '')
                            if text.isdigit():
                                players_online = int(text)
                    
                    cash_players = 0
                    cash_td = row.find('td', {'id': 'cash'})
                    if cash_td:
                        text = cash_td.get_text(strip=True).replace(',', '')
                        if text.isdigit():
                            cash_players = int(text)
                    
                    peak_24h = 0
                    peak_td = row.find('td', {'id': 'peak'})
                    if peak_td:
                        span = peak_td.find('span')
                        if span:
                            text = span.get_text(strip=True).replace(',', '')
                            if text.isdigit():
                                peak_24h = int(text)
                    
                    seven_day_avg = 0
                    avg_td = row.find('td', {'id': 'avg'})
                    if avg_td:
                        span = avg_td.find('span')
                        if span:
                            text = span.get_text(strip=True).replace(',', '')
                            if text.isdigit():
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
                    logger.debug(f"행 처리 중 오류: {e}")
                    continue
            
            return collected_data
            
        except Exception as e:
            logger.error(f"BeautifulSoup 파싱 실패: {e}")
            return []
    
    def _extract_number(self, row, td_id: str) -> int:
        """테이블 셀에서 숫자 추출"""
        try:
            td = row.find_element(By.ID, td_id)
            # span 태그 내부 텍스트 확인
            try:
                span = td.find_element(By.TAG_NAME, "span")
                text = span.text.strip().replace(',', '')
            except:
                text = td.text.strip().replace(',', '')
            
            if text.isdigit():
                return int(text)
        except:
            pass
        return 0

def get_access_token():
    """서비스 계정 키에서 액세스 토큰 생성"""
    try:
        possible_key_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'key', 'firebase-service-account-key.json'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'key', 'firebase-service-account-key.json'),
        ]
        
        key_path = None
        for path in possible_key_paths:
            if os.path.exists(path):
                key_path = path
                logger.info(f"Firebase 키 파일 발견: {key_path}")
                break
        
        if not key_path:
            logger.warning("Firebase 키 파일을 찾을 수 없습니다.")
            return None
            
        credentials = service_account.Credentials.from_service_account_file(
            key_path,
            scopes=['https://www.googleapis.com/auth/datastore']
        )
        
        credentials.refresh(Request())
        return credentials.token
        
    except Exception as e:
        logger.error(f"액세스 토큰 생성 실패: {e}")
        return None

def upload_to_firestore_rest(data, access_token=None):
    """Firestore REST API를 사용하여 데이터 업로드"""
    if not data:
        logger.warning("업로드할 데이터가 없습니다.")
        return False
    
    logger.info("Firestore REST API로 데이터 업로드 시작...")
    
    headers = {'Content-Type': 'application/json'}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    
    success_count = 0
    
    try:
        for site_data in data:
            site_name = site_data['site_name']
            collected_at_iso = site_data['collected_at']
            
            # 1. sites 컬렉션 업데이트
            site_url = f"{FIRESTORE_BASE_URL}/sites/{site_name}"
            site_doc = {
                "fields": {
                    "site_name": {"stringValue": site_name},
                    "category": {"stringValue": site_data['category']},
                    "last_updated_at": {"timestampValue": datetime.now(timezone.utc).isoformat()}
                }
            }
            
            response = requests.patch(site_url, json=site_doc, headers=headers)
            
            if response.status_code not in [200, 204]:
                logger.warning(f"사이트 문서 업데이트 실패 ({site_name}): {response.status_code}")
                continue
            
            # 2. traffic_logs 하위 컬렉션에 추가
            doc_id = collected_at_iso
            traffic_url = f"{FIRESTORE_BASE_URL}/sites/{site_name}/traffic_logs/{doc_id}"
            traffic_doc = {
                "fields": {
                    "players_online": {"integerValue": str(site_data['players_online'])},
                    "cash_players": {"integerValue": str(site_data['cash_players'])},
                    "peak_24h": {"integerValue": str(site_data['peak_24h'])},
                    "seven_day_avg": {"integerValue": str(site_data['seven_day_avg'])},
                    "collected_at": {"timestampValue": collected_at_iso}
                }
            }
            
            response = requests.patch(traffic_url, json=traffic_doc, headers=headers)
            
            if response.status_code in [200, 201]:
                success_count += 1
            else:
                logger.warning(f"트래픽 로그 생성 실패 ({site_name}): {response.status_code}")
        
        logger.info(f"성공적으로 {success_count}/{len(data)}개 사이트의 데이터를 Firestore에 업로드했습니다.")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Firestore REST API 업로드 중 오류 발생: {e}")
        return False

def save_backup_json(data):
    """백업용 JSON 저장"""
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

def run_enhanced_crawl():
    """향상된 크롤링 실행"""
    logger.info("=== Enhanced Selenium Crawling Start ===")
    logger.info(f"Current directory: {os.getcwd()}")
    
    try:
        # GitHub Actions 환경 확인
        is_github_actions = os.environ.get('GITHUB_ACTIONS') == 'true'
        
        # 크롤러 인스턴스 생성
        # GitHub Actions에서는 헤드리스 모드 강제, 프록시는 선택적
        crawler = EnhancedPokerScoutCrawler(
            use_proxy=not is_github_actions,  # GitHub Actions에서는 프록시 비활성화
            headless=True  # 항상 헤드리스 모드
        )
        
        # 재시도 로직이 포함된 크롤링 실행
        logger.info("크롤링 시작...")
        crawled_data = crawler.crawl_with_retry()
        
        if crawled_data:
            logger.info(f"크롤링 성공: {len(crawled_data)}개 사이트 발견")
            
            # 샘플 데이터 로깅
            for i, site in enumerate(crawled_data[:3]):
                logger.info(f"샘플 {i+1}: {site.get('site_name', 'Unknown')} - {site.get('players_online', 0)} players")
            
            # 총 플레이어 수 계산
            total_players = sum(site.get('players_online', 0) for site in crawled_data)
            logger.info(f"전체 온라인 플레이어 수: {total_players:,}")
            
            # Firebase 업로드
            access_token = get_access_token()
            if access_token:
                logger.info("액세스 토큰 생성 성공")
            else:
                logger.warning("액세스 토큰 없이 진행")
            
            upload_success = upload_to_firestore_rest(crawled_data, access_token)
            
            if not upload_success:
                save_backup_json(crawled_data)
            
            return True
        else:
            logger.error("ERROR: 데이터를 크롤링하지 못했습니다")
            return False
            
    except Exception as e:
        logger.error(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = run_enhanced_crawl()
    logger.info("=== Crawling Complete ===")
    sys.exit(0 if success else 1)