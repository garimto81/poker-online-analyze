#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
PokerScout 모든 온라인 포커 사이트 데이터 크롤링 및 Firebase 저장
"""

import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import json
import os

import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

# Firebase 서비스 계정 키 파일 경로
# 이 경로는 사용자님이 제공한 경로입니다.
SERVICE_ACCOUNT_KEY_PATH = "./key/firebase-service-account.json"

# Firebase 앱 초기화
try:
    if not firebase_admin._apps: # 이미 초기화되었는지 확인
        cred = credentials.Certificate(SERVICE_ACCOUNT_KEY_PATH)
        firebase_admin.initialize_app(cred)
    db = firestore.client()
    print("Firebase 앱이 성공적으로 초기화되었습니다.")
except Exception as e:
    print(f"Firebase 앱 초기화 중 오류 발생: {e}")
    # 초기화 실패 시 스크립트 종료
    exit()

def crawl_all_pokerscout_sites():
    """PokerScout에서 모든 온라인 포커 사이트 데이터 크롤링"""
    print("PokerScout 모든 온라인 포커 사이트 크롤링 시작")
    print("=" * 60)
    
    scraper = cloudscraper.create_scraper()
    
    start_time = datetime.now()
    print(f"크롤링 시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        response = scraper.get('https://www.pokerscout.com', timeout=20)
        response.raise_for_status()
        
        print(f"응답 코드: {response.status_code}")
        print(f"응답 크기: {len(response.content):,} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        table = soup.find('table', {'class': 'rankTable'})
        
        if not table:
            print("❌ rankTable을 찾을 수 없습니다!")
            return []
        
        rows = table.find_all('tr')[1:]  # 헤더 제외
        print(f"발견된 행 수: {len(rows)}")
        
        collected_data = []
        
        for i, row in enumerate(rows):
            try:
                # 광고 행 건너뛰기
                if 'cus_top_traffic_coin' in row.get('class', []):
                    print(f"행 {i+1}: 광고 행 건너뛰기 (class: {row.get('class')})")
                    continue
                
                # 사이트명 추출
                brand_title = row.find('span', {'class': 'brand-title'})
                if not brand_title:
                    continue
                
                site_name = brand_title.get_text(strip=True)
                if not site_name or len(site_name) < 2:
                    continue
                
                # Players Online 추출
                online_td = row.find('td', {'id': 'online'})
                players_online = 0
                online_raw = "N/A"
                if online_td:
                    online_span = online_td.find('span')
                    if online_span:
                        online_raw = online_span.get_text(strip=True)
                        online_text = online_raw.replace(',', '')
                        if online_text.isdigit():
                            players_online = int(online_text)
                
                # Cash Players 추출
                cash_players = 0
                cash_raw = "N/A"
                cash_td = row.find('td', {'id': 'cash'})
                if cash_td:
                    cash_raw = cash_td.get_text(strip=True)
                    cash_text = cash_raw.replace(',', '')
                    if cash_text.isdigit():
                        cash_players = int(cash_text)
                
                # Peak 24h 추출
                peak_24h = 0
                peak_td = row.find('td', {'id': 'peak'})
                if peak_td:
                    peak_text = peak_td.get_text(strip=True).replace(',', '')
                    if peak_text.isdigit():
                        peak_24h = int(peak_text)
                
                # 7일 평균 추출
                seven_day_avg = 0
                avg_td = row.find('td', {'id': 'avg'})
                if avg_td:
                    avg_text = avg_td.get_text(strip=True).replace(',', '')
                    if avg_text.isdigit():
                        seven_day_avg = int(avg_text)
                
                site_data = {
                    'rank': len(collected_data) + 1,
                    'site_name': site_name,
                    'players_online': players_online,
                    'players_online_raw': online_raw,
                    'cash_players': cash_players,
                    'cash_players_raw': cash_raw,
                    'peak_24h': peak_24h,
                    'seven_day_avg': seven_day_avg,
                    'extracted_at': datetime.now().isoformat()
                }
                
                collected_data.append(site_data)
                
                # 상위 10개 제한 제거됨 - 모든 사이트 크롤링
                    
            except Exception as e:
                print(f"행 {i+1} 처리 중 오류: {str(e)}")
                continue
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"\n크롤링 완료 시간: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"소요 시간: {duration:.2f}초")
        print(f"성공적으로 수집된 사이트: {len(collected_data)}개")
        
        return collected_data
        
    except Exception as e:
        print(f"❌ 크롤링 실패: {str(e)}")
        return []

def save_to_firebase(data):
    """크롤링된 데이터를 Firebase Firestore에 서브컬렉션 방식으로 저장"""
    if not data:
        print("저장할 데이터가 없습니다.")
        return

    print("\nFirebase Firestore에 데이터 저장 시작 (서브컬렉션 방식)...")
    batch = db.batch() # 배치 쓰기 사용으로 성능 향상

    current_date_str = datetime.now().strftime('%Y-%m-%d')

    for site_info in data:
        site_name = site_info['site_name']
        
        # 1. 'sites' 컬렉션에 사이트 정보 저장 (문서 ID는 site_name)
        # 이미 존재하는 사이트라면 업데이트, 없으면 새로 생성
        site_ref = db.collection('sites').document(site_name)
        batch.set(site_ref, {
            'name': site_name,
            'category': 'UNKNOWN', # 초기값, 필요시 수동 업데이트 또는 크롤링 로직 개선
            'created_at': firestore.SERVER_TIMESTAMP,
            'updated_at': firestore.SERVER_TIMESTAMP
        }, merge=True) # merge=True를 사용하여 기존 필드는 유지하고 새 필드만 추가/업데이트

        # 2. 'daily_stats' 서브컬렉션에 일별 통계 데이터 저장
        # 문서 ID는 현재 날짜 (YYYY-MM-DD)
        daily_stats_doc_ref = site_ref.collection('daily_stats').document(current_date_str)
        batch.set(daily_stats_doc_ref, {
            'players_online': site_info['players_online'],
            'cash_players': site_info['cash_players'],
            'peak_24h': site_info['peak_24h'],
            'seven_day_avg': site_info['seven_day_avg'],
            'extracted_at': firestore.SERVER_TIMESTAMP
        })
    
    try:
        batch.commit()
        print(f"총 {len(data)}개 사이트의 데이터가 Firebase Firestore에 서브컬렉션 방식으로 성공적으로 저장되었습니다.")
    except Exception as e:
        print(f"Firebase Firestore에 데이터 저장 중 오류 발생: {e}")

def display_results(data):
    """크롤링 결과 표시"""
    if not data:
        print("❌ 수집된 데이터가 없습니다.")
        return
    
    print("\n" + "=" * 80)
    print("PokerScout 모든 사이트 데이터")
    print("=" * 80)
    
    print(f"{'순위':<4} {'사이트명':<25} {'온라인':<12} {'캐시':<10} {'24h 피크':<10} {'7일 평균':<10}")
    print("-" * 80)
    
    for site in data:
        print(f"{site['rank']:<4} {site['site_name']:<25} {site['players_online']:>8,}명 {site['cash_players']:>7,}명 "
              f"{site['peak_24h']:>7,}명 {site['seven_day_avg']:>7,}명")
    
    # 총계
    total_online = sum(site['players_online'] for site in data)
    total_cash = sum(site['cash_players'] for site in data)
    
    print("-" * 80)
    print(f"{'총계':<30} {total_online:>8,}명 {total_cash:>7,}명")
    
    # GGNetwork 특별 확인
    gg_site = next((s for s in data if 'GGNetwork' in s['site_name']), None)
    if gg_site:
        print(f"GGNetwork 확인:")
        print(f"   순위: {gg_site['rank']}위")
        print(f"   온라인: {gg_site['players_online']:,}명")
        print(f"   원본 텍스트: '{gg_site['players_online_raw']}'")
    
    print(f"""
크롤링 시점: {data[0]['extracted_at']}""")

if __name__ == "__main__":
    # 크롤링 실행
    all_sites_data = crawl_all_pokerscout_sites()
    
    if all_sites_data:
        # 결과 표시
        display_results(all_sites_data)
        
        # 결과 저장 (Firebase)
        save_to_firebase(all_sites_data)
        
        print(f"\nPokerScout 모든 사이트 크롤링 및 Firebase 저장 완료!")
    else:
        print("❌ 크롤링에 실패했습니다.")