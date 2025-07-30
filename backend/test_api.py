#!/usr/bin/env python3
"""
API 엔드포인트 테스트 스크립트
"""

import requests
import json
from datetime import datetime

API_BASE_URL = "http://localhost:8000"

def test_api_connection():
    """API 서버 연결 테스트"""
    print("=" * 60)
    print("API 서버 연결 테스트")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/")
        if response.status_code == 200:
            print("✅ API 서버 연결 성공!")
            print(f"응답: {response.json()}")
            return True
        else:
            print(f"❌ API 서버 응답 오류: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ API 서버에 연결할 수 없습니다. 서버가 실행 중인지 확인하세요.")
        print("실행 명령: uvicorn main:app --reload")
        return False

def test_get_sites():
    """사이트 목록 조회 테스트"""
    print("\n" + "=" * 60)
    print("사이트 목록 조회 테스트")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/firebase/sites/")
        if response.status_code == 200:
            sites = response.json()
            print(f"✅ 사이트 목록 조회 성공! 총 {len(sites)}개 사이트")
            for site in sites[:3]:  # 상위 3개만 출력
                print(f"  - {site.get('site_name', 'Unknown')}: {site.get('category', 'Unknown')}")
            return True
        else:
            print(f"❌ 사이트 목록 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_current_ranking():
    """현재 순위 조회 테스트"""
    print("\n" + "=" * 60)
    print("현재 순위 조회 테스트")
    print("=" * 60)
    
    try:
        response = requests.get(f"{API_BASE_URL}/api/firebase/current_ranking/")
        if response.status_code == 200:
            ranking = response.json()
            print(f"✅ 현재 순위 조회 성공! 총 {len(ranking)}개 사이트")
            print("\n상위 5개 사이트:")
            print(f"{'순위':<5} {'사이트명':<25} {'온라인':<10} {'카테고리':<15}")
            print("-" * 60)
            for site in ranking[:5]:
                print(f"{site['rank']:<5} {site['site_name'][:24]:<25} {site['players_online']:<10,} {site['category']:<15}")
            return True
        else:
            print(f"❌ 현재 순위 조회 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_crawl_and_save():
    """크롤링 및 저장 테스트"""
    print("\n" + "=" * 60)
    print("크롤링 및 저장 테스트")
    print("=" * 60)
    
    proceed = input("크롤링을 실행하시겠습니까? (y/n): ")
    if proceed.lower() != 'y':
        print("크롤링 테스트 건너뜀")
        return False
    
    try:
        print("크롤링 시작... (약 10-30초 소요)")
        response = requests.post(f"{API_BASE_URL}/api/firebase/crawl_and_save_data/", timeout=60)
        if response.status_code == 200:
            result = response.json()
            print(f"✅ 크롤링 및 저장 성공!")
            print(f"  - 수집된 사이트: {result['count']}개")
            print(f"  - 타임스탬프: {result['timestamp']}")
            return True
        else:
            print(f"❌ 크롤링 실패: {response.status_code}")
            print(f"응답: {response.text}")
            return False
    except requests.exceptions.Timeout:
        print("❌ 크롤링 타임아웃 (60초 초과)")
        return False
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

def test_site_stats():
    """특정 사이트 통계 조회 테스트"""
    print("\n" + "=" * 60)
    print("특정 사이트 통계 조회 테스트")
    print("=" * 60)
    
    site_name = input("조회할 사이트명 (기본: GGNetwork): ") or "GGNetwork"
    
    try:
        # 최신 통계 조회
        response = requests.get(f"{API_BASE_URL}/api/firebase/sites/{site_name}/latest/")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ {site_name} 최신 통계 조회 성공!")
            if data['latest_stats']:
                stats = data['latest_stats']
                print(f"  - 온라인 플레이어: {stats['players_online']:,}명")
                print(f"  - 캐시 플레이어: {stats['cash_players']:,}명")
                print(f"  - 24시간 피크: {stats['peak_24h']:,}명")
                print(f"  - 7일 평균: {stats['seven_day_avg']:,}명")
            else:
                print("  - 통계 데이터가 없습니다.")
        elif response.status_code == 404:
            print(f"❌ 사이트를 찾을 수 없습니다: {site_name}")
        else:
            print(f"❌ 통계 조회 실패: {response.status_code}")
            
        # 7일 이력 조회
        response = requests.get(f"{API_BASE_URL}/api/firebase/sites/{site_name}/stats/?days=7")
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ {site_name} 7일 이력 조회 성공! 총 {data['count']}개 기록")
            
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        return False

if __name__ == "__main__":
    print("Poker Online Analyze - API 테스트\n")
    
    # API 서버 연결 테스트
    if test_api_connection():
        # 각 엔드포인트 테스트
        test_get_sites()
        test_current_ranking()
        test_site_stats()
        test_crawl_and_save()
    else:
        print("\n⚠️ API 서버 연결에 실패했습니다.")
        print("다음 명령으로 서버를 실행하세요:")
        print("cd backend && uvicorn main:app --reload")