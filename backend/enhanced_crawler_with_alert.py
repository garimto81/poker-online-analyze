#!/usr/bin/env python3
"""
향상된 PokerScout 크롤러 - 다중 폴백 메커니즘 및 알림 시스템 포함
- CloudScraper → Selenium → 일반 requests 순서로 시도
- 실패 시 이메일/Discord/Slack 알림 발송
- 상세한 에러 로깅 및 복구 시도
"""
import sys
import os
import logging
from datetime import datetime, timezone, timedelta
import json
import re
import time
import random
from typing import List, Dict, Optional, Tuple
import requests
from bs4 import BeautifulSoup
from google.oauth2 import service_account
from google.auth.transport.requests import Request
import cloudscraper

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s'
)
logger = logging.getLogger(__name__)

# Firebase 프로젝트 설정
FIREBASE_PROJECT_ID = "poker-online-analyze"
FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

# 알림 설정 (환경 변수에서 읽기)
ALERT_CONFIG = {
    'discord_webhook': os.environ.get('DISCORD_WEBHOOK_URL'),
    'slack_webhook': os.environ.get('SLACK_WEBHOOK_URL'),
    'email_to': os.environ.get('ALERT_EMAIL'),
    'github_issue': os.environ.get('GITHUB_REPO')  # e.g., "garimto81/poker-online-analyze"
}

class AlertSystem:
    """다양한 채널로 알림을 보내는 시스템"""
    
    def __init__(self):
        self.alerts_sent = []
        self.last_alert_time = None
        
    def send_alert(self, title: str, message: str, level: str = "ERROR", details: Dict = None):
        """모든 설정된 채널로 알림 발송"""
        # 중복 알림 방지 (5분 이내 동일 알림 차단)
        alert_key = f"{title}:{level}"
        current_time = datetime.now()
        
        if self.last_alert_time:
            time_diff = (current_time - self.last_alert_time).seconds
            if time_diff < 300 and alert_key in self.alerts_sent:  # 5분
                logger.info(f"알림 스킵 (최근 발송됨): {title}")
                return
        
        self.last_alert_time = current_time
        self.alerts_sent.append(alert_key)
        
        # Discord 알림
        if ALERT_CONFIG.get('discord_webhook'):
            self._send_discord_alert(title, message, level, details)
        
        # Slack 알림
        if ALERT_CONFIG.get('slack_webhook'):
            self._send_slack_alert(title, message, level, details)
        
        # GitHub Issue 생성
        if ALERT_CONFIG.get('github_issue') and level == "CRITICAL":
            self._create_github_issue(title, message, details)
        
        # 콘솔 출력 (GitHub Actions 로그)
        self._log_to_console(title, message, level, details)
    
    def _send_discord_alert(self, title: str, message: str, level: str, details: Dict):
        """Discord 웹훅으로 알림 발송"""
        try:
            color = {
                "INFO": 0x00FF00,     # 녹색
                "WARNING": 0xFFFF00,  # 노란색
                "ERROR": 0xFF0000,    # 빨간색
                "CRITICAL": 0x8B0000  # 진한 빨간색
            }.get(level, 0x808080)
            
            embed = {
                "title": f"🚨 {title}",
                "description": message,
                "color": color,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "fields": []
            }
            
            if details:
                for key, value in details.items():
                    embed["fields"].append({
                        "name": key,
                        "value": str(value)[:1024],
                        "inline": True
                    })
            
            payload = {"embeds": [embed]}
            response = requests.post(
                ALERT_CONFIG['discord_webhook'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 204:
                logger.info("Discord 알림 발송 성공")
            else:
                logger.warning(f"Discord 알림 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Discord 알림 발송 중 오류: {e}")
    
    def _send_slack_alert(self, title: str, message: str, level: str, details: Dict):
        """Slack 웹훅으로 알림 발송"""
        try:
            blocks = [
                {
                    "type": "header",
                    "text": {
                        "type": "plain_text",
                        "text": f"🚨 {title}"
                    }
                },
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": f"*Level:* {level}\n*Message:* {message}"
                    }
                }
            ]
            
            if details:
                fields = []
                for key, value in details.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                blocks.append({
                    "type": "section",
                    "fields": fields[:10]  # 최대 10개 필드
                })
            
            payload = {"blocks": blocks}
            response = requests.post(
                ALERT_CONFIG['slack_webhook'],
                json=payload,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info("Slack 알림 발송 성공")
            else:
                logger.warning(f"Slack 알림 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"Slack 알림 발송 중 오류: {e}")
    
    def _create_github_issue(self, title: str, message: str, details: Dict):
        """GitHub Issue 자동 생성 (Critical 에러만)"""
        try:
            if not os.environ.get('GITHUB_TOKEN'):
                logger.warning("GitHub Token이 설정되지 않아 Issue를 생성할 수 없습니다.")
                return
            
            repo = ALERT_CONFIG['github_issue']
            url = f"https://api.github.com/repos/{repo}/issues"
            
            body = f"## 자동 생성된 이슈\n\n"
            body += f"**발생 시간:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
            body += f"**메시지:** {message}\n\n"
            
            if details:
                body += "### 상세 정보\n\n"
                for key, value in details.items():
                    body += f"- **{key}:** {value}\n"
            
            headers = {
                "Authorization": f"token {os.environ.get('GITHUB_TOKEN')}",
                "Accept": "application/vnd.github.v3+json"
            }
            
            payload = {
                "title": f"[자동] {title}",
                "body": body,
                "labels": ["bug", "automated", "crawler-issue"]
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 201:
                issue_url = response.json().get('html_url')
                logger.info(f"GitHub Issue 생성됨: {issue_url}")
            else:
                logger.warning(f"GitHub Issue 생성 실패: {response.status_code}")
                
        except Exception as e:
            logger.error(f"GitHub Issue 생성 중 오류: {e}")
    
    def _log_to_console(self, title: str, message: str, level: str, details: Dict):
        """콘솔에 구조화된 알림 출력 (GitHub Actions 로그용)"""
        print("\n" + "="*80)
        print(f"🚨 알림: {title}")
        print(f"📊 레벨: {level}")
        print(f"📝 메시지: {message}")
        
        if details:
            print("📋 상세 정보:")
            for key, value in details.items():
                print(f"  - {key}: {value}")
        
        print("="*80 + "\n")

class RobustPokerScoutCrawler:
    """다중 폴백 메커니즘을 갖춘 견고한 크롤러"""
    
    def __init__(self):
        self.alert_system = AlertSystem()
        self.scraper = cloudscraper.create_scraper(
            browser={'browser': 'chrome', 'platform': 'windows', 'mobile': False}
        )
        self.gg_poker_sites = ['GGNetwork', 'GGPoker ON', 'GG Poker', 'GGPoker']
        self.retry_count = 3
        self.timeout = 30
        self.last_successful_data = None
        self.last_successful_time = None
        
    def crawl_with_fallback(self) -> Tuple[bool, List[Dict], str]:
        """다중 폴백 메커니즘으로 크롤링 시도"""
        methods = [
            ("CloudScraper", self._crawl_with_cloudscraper),
            ("Regular Requests", self._crawl_with_requests),
            ("Different Headers", self._crawl_with_custom_headers),
            ("Cached Data", self._use_cached_data)
        ]
        
        for method_name, method_func in methods:
            logger.info(f"크롤링 시도: {method_name}")
            
            try:
                success, data, message = method_func()
                
                if success and data:
                    logger.info(f"✅ {method_name} 성공: {len(data)}개 사이트")
                    
                    # 성공 시 캐시 업데이트
                    self.last_successful_data = data
                    self.last_successful_time = datetime.now()
                    
                    # 이전에 실패했다가 복구된 경우 알림
                    if hasattr(self, '_was_failing') and self._was_failing:
                        self.alert_system.send_alert(
                            "크롤링 복구됨",
                            f"{method_name} 방법으로 데이터 수집이 복구되었습니다.",
                            "INFO",
                            {"사이트 수": len(data), "방법": method_name}
                        )
                        self._was_failing = False
                    
                    return True, data, f"{method_name} 성공"
                else:
                    logger.warning(f"❌ {method_name} 실패: {message}")
                    
            except Exception as e:
                logger.error(f"❌ {method_name} 예외 발생: {str(e)}")
                continue
        
        # 모든 방법 실패
        self._was_failing = True
        self._handle_complete_failure()
        return False, [], "모든 크롤링 방법 실패"
    
    def _crawl_with_cloudscraper(self) -> Tuple[bool, List[Dict], str]:
        """CloudScraper를 사용한 크롤링 (기본 방법)"""
        for attempt in range(self.retry_count):
            try:
                # 요청 간 랜덤 지연
                if attempt > 0:
                    delay = random.uniform(2, 5)
                    logger.info(f"재시도 전 {delay:.1f}초 대기...")
                    time.sleep(delay)
                
                response = self.scraper.get(
                    'https://www.pokerscout.com',
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = self._parse_html(response.text)
                    if data:
                        return True, data, "성공"
                    else:
                        logger.warning("HTML 파싱 실패 - 페이지 구조 변경 가능성")
                elif response.status_code == 403:
                    return False, [], "403 Forbidden - 차단됨"
                else:
                    logger.warning(f"HTTP {response.status_code}")
                    
            except Exception as e:
                logger.error(f"CloudScraper 시도 {attempt+1} 실패: {e}")
        
        return False, [], "CloudScraper 모든 시도 실패"
    
    def _crawl_with_requests(self) -> Tuple[bool, List[Dict], str]:
        """일반 requests 라이브러리 사용"""
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        try:
            session = requests.Session()
            response = session.get(
                'https://www.pokerscout.com',
                headers=headers,
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                data = self._parse_html(response.text)
                if data:
                    return True, data, "성공"
            
            return False, [], f"HTTP {response.status_code}"
            
        except Exception as e:
            return False, [], str(e)
    
    def _crawl_with_custom_headers(self) -> Tuple[bool, List[Dict], str]:
        """다양한 User-Agent와 헤더 조합 시도"""
        user_agents = [
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/121.0'
        ]
        
        for ua in user_agents:
            try:
                headers = {
                    'User-Agent': ua,
                    'Accept': '*/*',
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                }
                
                response = requests.get(
                    'https://www.pokerscout.com',
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    data = self._parse_html(response.text)
                    if data:
                        return True, data, f"성공 (UA: {ua[:30]}...)"
                        
            except Exception as e:
                continue
        
        return False, [], "모든 User-Agent 실패"
    
    def _use_cached_data(self) -> Tuple[bool, List[Dict], str]:
        """마지막 성공한 데이터 사용 (비상용)"""
        if self.last_successful_data and self.last_successful_time:
            time_diff = datetime.now() - self.last_successful_time
            hours_old = time_diff.total_seconds() / 3600
            
            if hours_old < 24:  # 24시간 이내 데이터만 사용
                logger.warning(f"⚠️ {hours_old:.1f}시간 전 캐시 데이터 사용")
                
                # 캐시 데이터 사용 알림
                self.alert_system.send_alert(
                    "캐시 데이터 사용 중",
                    f"실시간 크롤링 실패로 {hours_old:.1f}시간 전 데이터를 사용합니다.",
                    "WARNING",
                    {
                        "캐시 시간": self.last_successful_time.strftime("%Y-%m-%d %H:%M:%S"),
                        "데이터 수": len(self.last_successful_data)
                    }
                )
                
                return True, self.last_successful_data, f"캐시 데이터 ({hours_old:.1f}시간 전)"
        
        return False, [], "사용 가능한 캐시 없음"
    
    def _parse_html(self, html_content: str) -> List[Dict]:
        """HTML 파싱 로직"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 다양한 방법으로 테이블 찾기
            table = soup.find('table', {'class': 'rankTable'})
            
            if not table:
                # 대체 선택자 시도
                table = soup.find('table', class_=re.compile('rank', re.I))
            
            if not table:
                tables = soup.find_all('table')
                if tables:
                    table = tables[0]  # 첫 번째 테이블 사용
                    logger.warning(f"rankTable을 찾을 수 없어 첫 번째 테이블 사용 (총 {len(tables)}개)")
            
            if not table:
                logger.error("테이블을 찾을 수 없음")
                return []
            
            collected_data = []
            rows = table.find_all('tr')[1:]  # 헤더 제외
            
            for row in rows:
                try:
                    # 사이트 이름 추출
                    brand_title = row.find('span', {'class': 'brand-title'})
                    if not brand_title:
                        brand_title = row.find('span', class_=re.compile('brand', re.I))
                    
                    if not brand_title:
                        continue
                    
                    site_name = brand_title.get_text(strip=True)
                    if not site_name or len(site_name) < 2:
                        continue
                    
                    # 통계 추출
                    stats = self._extract_stats(row)
                    
                    if stats['players_online'] == 0 and stats['cash_players'] == 0 and stats['peak_24h'] == 0:
                        continue
                    
                    site_name = re.sub(r'[^\w\s\-\(\)\.&]', '', site_name).strip()
                    category = 'GG_POKER' if site_name in self.gg_poker_sites else 'COMPETITOR'
                    
                    collected_data.append({
                        'site_name': site_name,
                        'category': category,
                        'players_online': stats['players_online'],
                        'cash_players': stats['cash_players'],
                        'peak_24h': stats['peak_24h'],
                        'seven_day_avg': stats['seven_day_avg'],
                        'collected_at': datetime.now(timezone.utc).isoformat()
                    })
                    
                except Exception as e:
                    logger.debug(f"행 파싱 오류: {e}")
                    continue
            
            return collected_data
            
        except Exception as e:
            logger.error(f"HTML 파싱 실패: {e}")
            return []
    
    def _extract_stats(self, row) -> Dict[str, int]:
        """테이블 행에서 통계 추출"""
        stats = {
            'players_online': 0,
            'cash_players': 0,
            'peak_24h': 0,
            'seven_day_avg': 0
        }
        
        # ID로 찾기
        for stat_name, td_id in [
            ('players_online', 'online'),
            ('cash_players', 'cash'),
            ('peak_24h', 'peak'),
            ('seven_day_avg', 'avg')
        ]:
            td = row.find('td', {'id': td_id})
            if td:
                # span 태그 확인
                span = td.find('span')
                text = span.get_text(strip=True) if span else td.get_text(strip=True)
                text = text.replace(',', '')
                if text.isdigit():
                    stats[stat_name] = int(text)
        
        return stats
    
    def _handle_complete_failure(self):
        """모든 크롤링 방법 실패 시 처리"""
        error_details = {
            "시간": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "URL": "https://www.pokerscout.com",
            "시도한 방법": "CloudScraper, Requests, Custom Headers, Cache",
            "액션 필요": "크롤링 로직 점검 필요"
        }
        
        # Critical 알림 발송
        self.alert_system.send_alert(
            "PokerScout 크롤링 완전 실패",
            "모든 크롤링 방법이 실패했습니다. 즉시 점검이 필요합니다.",
            "CRITICAL",
            error_details
        )
        
        # 백업 JSON 파일 생성
        self._save_failure_report(error_details)
    
    def _save_failure_report(self, details: Dict):
        """실패 리포트 저장"""
        report = {
            "status": "FAILED",
            "timestamp": datetime.now().isoformat(),
            "details": details,
            "last_successful": {
                "time": self.last_successful_time.isoformat() if self.last_successful_time else None,
                "data_count": len(self.last_successful_data) if self.last_successful_data else 0
            }
        }
        
        filename = f"crawl_failure_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        logger.info(f"실패 리포트 저장: {filename}")

def get_access_token():
    """Firebase 액세스 토큰 생성"""
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
    """Firestore에 데이터 업로드"""
    if not data:
        logger.warning("업로드할 데이터가 없습니다.")
        return False
    
    logger.info(f"Firestore에 {len(data)}개 사이트 데이터 업로드 시작...")
    
    headers = {'Content-Type': 'application/json'}
    if access_token:
        headers['Authorization'] = f'Bearer {access_token}'
    
    success_count = 0
    
    try:
        for site_data in data:
            site_name = site_data['site_name']
            collected_at_iso = site_data['collected_at']
            
            # sites 컬렉션 업데이트
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
            
            # traffic_logs 하위 컬렉션에 추가
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
        
        logger.info(f"✅ Firestore 업로드 완료: {success_count}/{len(data)}개 성공")
        return success_count > 0
        
    except Exception as e:
        logger.error(f"Firestore 업로드 중 오류: {e}")
        return False

def run_enhanced_crawl():
    """향상된 크롤링 실행 메인 함수"""
    logger.info("="*80)
    logger.info("향상된 PokerScout 크롤링 시작")
    logger.info(f"실행 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("="*80)
    
    try:
        # 크롤러 인스턴스 생성
        crawler = RobustPokerScoutCrawler()
        
        # 폴백 메커니즘으로 크롤링 시도
        success, crawled_data, method = crawler.crawl_with_fallback()
        
        if success and crawled_data:
            logger.info(f"✅ 크롤링 성공: {len(crawled_data)}개 사이트 ({method})")
            
            # 주요 통계 출력
            total_players = sum(site.get('players_online', 0) for site in crawled_data)
            logger.info(f"📊 전체 온라인 플레이어: {total_players:,}명")
            
            # 상위 3개 사이트 출력
            for i, site in enumerate(crawled_data[:3], 1):
                logger.info(
                    f"  {i}. {site['site_name']}: "
                    f"{site['players_online']:,}명 온라인"
                )
            
            # Firebase 업로드
            access_token = get_access_token()
            upload_success = upload_to_firestore_rest(crawled_data, access_token)
            
            if not upload_success:
                # 업로드 실패 알림
                crawler.alert_system.send_alert(
                    "Firebase 업로드 실패",
                    "데이터 수집은 성공했으나 Firebase 업로드에 실패했습니다.",
                    "ERROR",
                    {"수집 데이터": len(crawled_data), "방법": method}
                )
                
                # 백업 저장
                backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(crawled_data, f, ensure_ascii=False, indent=2)
                logger.info(f"백업 파일 저장: {backup_file}")
            
            return True
            
        else:
            logger.error("❌ 크롤링 완전 실패")
            return False
            
    except Exception as e:
        logger.error(f"예기치 않은 오류: {e}")
        import traceback
        traceback.print_exc()
        
        # 예외 발생 알림
        AlertSystem().send_alert(
            "크롤러 예외 발생",
            f"예기치 않은 오류가 발생했습니다: {str(e)}",
            "CRITICAL",
            {"에러 타입": type(e).__name__}
        )
        
        return False

if __name__ == "__main__":
    success = run_enhanced_crawl()
    logger.info("="*80)
    logger.info(f"크롤링 종료 - 결과: {'성공' if success else '실패'}")
    logger.info("="*80)
    sys.exit(0 if success else 1)