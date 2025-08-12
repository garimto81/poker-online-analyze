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
FIREBASE_REALTIME_DB_URL = "https://poker-analyzer-ggp-default-rtdb.firebaseio.com"

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
        self.gg_poker_sites = [
            'GGNetwork', 'GGPoker ON', 'GG Poker', 'GGPoker', 
            'GG Network', 'GGPoker.com', 'GG', 'Natural8',
            'GGPoker Global', 'GGPoker EU', 'BetKings', 'GGasia'
        ]
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
                    # 광고 행이나 특별 행 스킵
                    if self._is_advertisement_row(row):
                        logger.debug("광고 행 스킵됨")
                        continue
                    
                    # 순위 번호 추출
                    rank = self._extract_rank(row)
                    
                    # 사이트 이름 추출 (여러 방법 시도)
                    site_name = self._extract_site_name(row)
                    
                    if not site_name or len(site_name) < 2:
                        logger.debug(f"사이트명 추출 실패, 행 스킵: {site_name}")
                        continue
                    
                    # WPT Global, GGPoker ON 등 특정 사이트 확인
                    if 'WPT' in site_name or 'GGPoker ON' in site_name:
                        logger.info(f"주요 사이트 감지: {site_name}")
                    
                    # 통계 추출
                    stats = self._extract_stats(row)
                    
                    if stats['players_online'] == 0 and stats['cash_players'] == 0 and stats['peak_24h'] == 0:
                        continue
                    
                    # 사이트명 정리
                    site_name = self._clean_site_name(site_name)
                    
                    # 카테고리 결정 (더 포괄적인 매칭)
                    category = self._determine_category(site_name)
                    
                    collected_data.append({
                        'rank': rank,
                        'site_name': site_name,
                        'category': category,
                        'players_online': stats['players_online'],
                        'cash_players': stats['cash_players'],
                        'peak_24h': stats['peak_24h'],
                        'seven_day_avg': stats['seven_day_avg'],
                        'collected_at': datetime.now(timezone.utc).isoformat()
                    })
                    
                    # 주요 사이트 로그
                    if category == 'GG_POKER' or 'WPT' in site_name:
                        logger.info(f"#{rank} {site_name}: {stats['players_online']:,}명 온라인 ({category})")
                    
                except Exception as e:
                    logger.debug(f"행 파싱 오류: {e}")
                    continue
            
            return collected_data
            
        except Exception as e:
            logger.error(f"HTML 파싱 실패: {e}")
            return []
    
    def _extract_stats(self, row) -> Dict[str, int]:
        """테이블 행에서 통계 추출 (여러 방법 시도)"""
        stats = {
            'players_online': 0,
            'cash_players': 0,
            'peak_24h': 0,
            'seven_day_avg': 0
        }
        
        try:
            # 방법 1: ID로 찾기
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
            
            # 방법 2: 순서로 추출 (ID로 찾기 실패 시)
            if all(v == 0 for v in stats.values()):
                tds = row.find_all('td')
                if len(tds) >= 6:  # 순위, 사이트명, 온라인, 캐시, 피크, 평균
                    stat_indices = [2, 3, 4, 5]  # 온라인, 캐시, 피크, 평균 순서
                    stat_names = ['players_online', 'cash_players', 'peak_24h', 'seven_day_avg']
                    
                    for i, stat_name in enumerate(stat_names):
                        if stat_indices[i] < len(tds):
                            td = tds[stat_indices[i]]
                            text = td.get_text(strip=True).replace(',', '')
                            # 숫자만 추출
                            numbers = re.findall(r'\d+', text)
                            if numbers:
                                stats[stat_name] = int(numbers[0])
            
            # 방법 3: 클래스명으로 찾기
            if all(v == 0 for v in stats.values()):
                for stat_name in ['players_online', 'cash_players', 'peak_24h', 'seven_day_avg']:
                    # 일반적인 클래스명 패턴들
                    class_patterns = [
                        f'{stat_name}', stat_name.replace('_', '-'), 
                        stat_name.split('_')[0], 'stat', 'number'
                    ]
                    
                    for pattern in class_patterns:
                        td = row.find('td', class_=re.compile(pattern, re.I))
                        if td:
                            text = td.get_text(strip=True).replace(',', '')
                            numbers = re.findall(r'\d+', text)
                            if numbers:
                                stats[stat_name] = int(numbers[0])
                                break
            
            # 로깅
            if any(v > 0 for v in stats.values()):
                logger.debug(f"통계 추출 성공: {stats}")
            else:
                logger.debug("통계 추출 실패 - 모든 값이 0")
                
        except Exception as e:
            logger.debug(f"통계 추출 중 오류: {e}")
        
        return stats
    
    def _is_advertisement_row(self, row) -> bool:
        """광고 행이나 특별한 행인지 확인"""
        try:
            # 광고 관련 키워드 확인
            text_content = row.get_text(strip=True).lower()
            
            # 일반적인 광고 키워드들
            ad_keywords = [
                'best bonus', 'bonus', 'advertisement', 'ad', 'promo',
                'promotion', 'sponsor', 'featured', 'coinpoker'
            ]
            
            for keyword in ad_keywords:
                if keyword in text_content:
                    return True
            
            # 링크나 광고 class가 있는지 확인
            if row.find('a', class_=re.compile('ad|bonus|promo', re.I)):
                return True
            
            # 비정상적으로 많은 링크가 있는 행 (광고 가능성)
            links = row.find_all('a')
            if len(links) > 3:
                return True
            
            # 통계 데이터가 없거나 비정상적인 행
            stats_cells = row.find_all('td')
            if len(stats_cells) < 4:  # 최소 4개 컬럼(순위, 사이트명, 플레이어수, 통계) 필요
                return True
                
            return False
            
        except Exception as e:
            logger.debug(f"광고 행 검사 중 오류: {e}")
            return False
    
    def _extract_rank(self, row) -> int:
        """순위 번호 추출"""
        try:
            # 첫 번째 td에서 순위 찾기
            first_td = row.find('td')
            if first_td:
                # 숫자만 추출
                rank_text = first_td.get_text(strip=True)
                # 순위 번호 패턴 매칭 (1, 2, 3... 또는 #1, #2, #3...)
                rank_match = re.search(r'#?(\d+)', rank_text)
                if rank_match:
                    return int(rank_match.group(1))
            
            # 대안: class나 id로 순위 셀 찾기
            rank_cell = row.find('td', class_=re.compile('rank|position', re.I))
            if rank_cell:
                rank_text = rank_cell.get_text(strip=True)
                rank_match = re.search(r'(\d+)', rank_text)
                if rank_match:
                    return int(rank_match.group(1))
            
            return 0  # 순위를 찾을 수 없음
            
        except Exception as e:
            logger.debug(f"순위 추출 중 오류: {e}")
            return 0
    
    def _extract_site_name(self, row) -> str:
        """사이트 이름 추출 (여러 방법 시도)"""
        try:
            # 방법 1: brand-title class
            brand_title = row.find('span', {'class': 'brand-title'})
            if brand_title:
                site_name = brand_title.get_text(strip=True)
                if site_name and len(site_name) > 1:
                    return site_name
            
            # 방법 2: brand 관련 class 검색
            brand_span = row.find('span', class_=re.compile('brand', re.I))
            if brand_span:
                site_name = brand_span.get_text(strip=True)
                if site_name and len(site_name) > 1:
                    return site_name
            
            # 방법 3: 사이트 링크에서 추출
            site_link = row.find('a', class_=re.compile('site|brand', re.I))
            if site_link:
                site_name = site_link.get_text(strip=True)
                if site_name and len(site_name) > 1:
                    return site_name
            
            # 방법 4: 두 번째 td에서 텍스트 추출 (순위 다음 셀)
            tds = row.find_all('td')
            if len(tds) >= 2:
                site_cell = tds[1]  # 두 번째 셀 (첫 번째는 보통 순위)
                # 링크가 있으면 링크 텍스트 사용
                link = site_cell.find('a')
                if link:
                    site_name = link.get_text(strip=True)
                else:
                    site_name = site_cell.get_text(strip=True)
                
                if site_name and len(site_name) > 1:
                    return site_name
            
            # 방법 5: 강력한 패턴으로 사이트명 검색
            all_text = row.get_text()
            # 알려진 포커 사이트 패턴들
            poker_sites = [
                r'PokerStars?', r'GGPoker(?:\s+ON)?', r'WPT\s+Global?', 
                r'partypoker', r'888poker', r'BetMGM', r'Natural8',
                r'CoinPoker', r'Ignition', r'BetOnline', r'Americas Cardroom',
                r'Bodog', r'SportsBetting', r'Bovada', r'WSOP'
            ]
            
            for pattern in poker_sites:
                match = re.search(pattern, all_text, re.IGNORECASE)
                if match:
                    return match.group(0).strip()
            
            return ""
            
        except Exception as e:
            logger.debug(f"사이트명 추출 중 오류: {e}")
            return ""
    
    def _clean_site_name(self, site_name: str) -> str:
        """사이트명 정리 및 표준화"""
        if not site_name:
            return ""
        
        # 특수문자 제거 (허용: 문자, 숫자, 공백, 하이픈, 괄호, 점, &)
        cleaned = re.sub(r'[^\w\s\-\(\)\.&]', '', site_name).strip()
        
        # 연속 공백 제거
        cleaned = re.sub(r'\s+', ' ', cleaned)
        
        # 알려진 사이트명 표준화
        standardizations = {
            'gg poker': 'GGPoker',
            'ggpoker on': 'GGPoker ON',
            'wpt global': 'WPT Global',
            'pokerstars': 'PokerStars',
            'party poker': 'partypoker',
            '888 poker': '888poker'
        }
        
        cleaned_lower = cleaned.lower()
        for old, new in standardizations.items():
            if old in cleaned_lower:
                cleaned = new
                break
        
        return cleaned
    
    def _determine_category(self, site_name: str) -> str:
        """사이트 카테고리 결정 (더 포괄적인 매칭)"""
        if not site_name:
            return 'UNKNOWN'
        
        site_lower = site_name.lower()
        
        # GG Network 관련 사이트들 (더 포괄적)
        gg_patterns = [
            'gg', 'natural8', 'betkings', 'ggasia', 'ggpoker'
        ]
        
        for pattern in gg_patterns:
            if pattern in site_lower:
                return 'GG_POKER'
        
        # 다른 주요 네트워크들
        if any(keyword in site_lower for keyword in ['pokerstars', 'stars']):
            return 'POKERSTARS'
        elif any(keyword in site_lower for keyword in ['wpt', 'world poker tour']):
            return 'WPT'
        elif any(keyword in site_lower for keyword in ['party', 'bwin']):
            return 'PARTY_POKER'
        
        return 'COMPETITOR'
    
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

def upload_to_realtime_database(data):
    """Realtime Database에 데이터 업로드 (GitHub Pages용)"""
    if not data:
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
        url = f"{FIREBASE_REALTIME_DB_URL}/pokerData/{date_key}.json"
        response = requests.put(url, json=db_data)
        
        if response.status_code == 200:
            logger.info(f"✅ Realtime Database 업로드 성공: {date_key}")
            
            # 2. latest 경로에도 저장 (최신 데이터 빠른 접근용)
            latest_url = f"{FIREBASE_REALTIME_DB_URL}/latest.json"
            requests.put(latest_url, json=db_data)
            
            return True
        else:
            logger.error(f"❌ Realtime Database 업로드 실패: {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Realtime Database 업로드 중 오류: {e}")
        return False

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
            
            # sites 컬렉션 업데이트 (순위 정보 포함)
            site_url = f"{FIRESTORE_BASE_URL}/sites/{site_name}"
            site_doc = {
                "fields": {
                    "site_name": {"stringValue": site_name},
                    "category": {"stringValue": site_data['category']},
                    "rank": {"integerValue": str(site_data.get('rank', 999))},  # 순위 추가
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
                    "rank": {"integerValue": str(site_data.get('rank', 0))},
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
            
            # Firebase 업로드 (두 가지 방식 모두 시도)
            # 1. Realtime Database 업로드 (GitHub Pages용)
            realtime_success = upload_to_realtime_database(crawled_data)
            
            # 2. Firestore 업로드 (기존 방식)
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