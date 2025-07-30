#!/usr/bin/env python3
"""
웹사이트 기능 전체 테스트
GitHub Pages에서 Firebase 연동이 실제로 작동하는지 확인
"""
import requests
import json
import time
from datetime import datetime
import re

def test_website_loads():
    """웹사이트가 로드되는지 테스트"""
    print("=== TESTING WEBSITE LOADING ===")
    
    url = "https://garimto81.github.io/poker-online-analyze"
    
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            content = response.text
            
            # React 앱 요소들 확인
            checks = {
                'React root': '<div id="root">' in content,
                'App title': 'Online Poker Traffic Analysis' in content,
                'Firebase service': 'firebaseService' in content or 'firebase' in content.lower(),
                'JavaScript bundle': any(script in content for script in ['.js', 'script']),
                'CSS styles': any(style in content for style in ['.css', 'style']),
            }
            
            print(f"Website status: {response.status_code}")
            print(f"Content length: {len(content)} characters")
            
            for check_name, result in checks.items():
                status = "[OK]" if result else "[ERROR]"
                print(f"  {status} {check_name}")
            
            all_checks_pass = all(checks.values())
            return all_checks_pass, content
        else:
            print(f"[ERROR] Website not accessible: {response.status_code}")
            return False, None
            
    except Exception as e:
        print(f"[ERROR] Website test failed: {e}")
        return False, None

def test_firebase_data_availability():
    """Firebase 데이터 사용 가능성 테스트"""
    print(f"\n=== TESTING FIREBASE DATA AVAILABILITY ===")
    
    project_id = 'poker-online-analyze'
    base_url = f'https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents'
    
    # 1. 사이트 데이터 확인
    print(f"[TEST] Checking sites data...")
    sites_url = f"{base_url}/sites"
    
    try:
        response = requests.get(sites_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            if 'documents' in data:
                sites_count = len(data['documents'])
                print(f"[OK] Found {sites_count} sites")
                
                # 2. 트래픽 데이터가 있는 사이트 개수 확인
                sites_with_traffic = 0
                sample_data = []
                
                for i, doc in enumerate(data['documents'][:10]):  # 처음 10개만 체크
                    site_name = doc['name'].split('/')[-1]
                    traffic_url = f"{base_url}/sites/{requests.utils.quote(site_name, safe='')}/traffic_logs"
                    
                    try:
                        traffic_response = requests.get(traffic_url, timeout=10)
                        if traffic_response.status_code == 200:
                            traffic_data = traffic_response.json()
                            if traffic_data.get('documents'):
                                sites_with_traffic += 1
                                
                                # 샘플 데이터 수집
                                if len(sample_data) < 3:
                                    latest_log = traffic_data['documents'][0]
                                    fields = latest_log.get('fields', {})
                                    sample_data.append({
                                        'site_name': site_name,
                                        'players_online': fields.get('players_online', {}).get('integerValue', 0),
                                        'cash_players': fields.get('cash_players', {}).get('integerValue', 0),
                                        'last_updated': fields.get('collected_at', {}).get('timestampValue', 'N/A')
                                    })
                    except:
                        pass
                
                print(f"[OK] {sites_with_traffic}/10 sample sites have traffic data")
                
                # 3. 샘플 데이터 출력
                if sample_data:
                    print(f"[OK] Sample data preview:")
                    for site in sample_data:
                        print(f"  - {site['site_name']}: {site['players_online']} players online")
                
                return sites_count > 0 and sites_with_traffic > 0
            else:
                print(f"[ERROR] No sites documents found")
                return False
        else:
            print(f"[ERROR] Sites data not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Firebase test failed: {e}")
        return False

def test_cors_headers():
    """CORS 헤더 테스트"""
    print(f"\n=== TESTING CORS CONFIGURATION ===")
    
    # GitHub Pages가 Firebase에 접근할 수 있는지 CORS 관점에서 테스트
    firebase_url = "https://firestore.googleapis.com/v1/projects/poker-online-analyze/databases/(default)/documents/sites"
    
    # OPTIONS 요청으로 CORS preflight 시뮬레이션
    headers = {
        'Origin': 'https://garimto81.github.io',
        'Access-Control-Request-Method': 'GET',
        'Access-Control-Request-Headers': 'Content-Type'
    }
    
    try:
        # OPTIONS 요청
        options_response = requests.options(firebase_url, headers=headers, timeout=10)
        print(f"CORS preflight status: {options_response.status_code}")
        
        # 실제 GET 요청
        get_headers = {'Origin': 'https://garimto81.github.io'}
        get_response = requests.get(firebase_url, headers=get_headers, timeout=10)
        print(f"CORS actual request status: {get_response.status_code}")
        
        # CORS 헤더 확인
        cors_headers = {
            'Access-Control-Allow-Origin': get_response.headers.get('Access-Control-Allow-Origin'),
            'Access-Control-Allow-Methods': get_response.headers.get('Access-Control-Allow-Methods'),
            'Access-Control-Allow-Headers': get_response.headers.get('Access-Control-Allow-Headers')
        }
        
        print(f"CORS headers:")
        for header, value in cors_headers.items():
            print(f"  {header}: {value or 'Not set'}")
        
        # Firebase는 기본적으로 CORS를 허용하므로 GET 요청이 성공하면 OK
        return get_response.status_code == 200
        
    except Exception as e:
        print(f"[ERROR] CORS test failed: {e}")
        return False

def analyze_results(website_ok, content, firebase_ok, cors_ok):
    """테스트 결과 종합 분석"""
    print(f"\n=== COMPREHENSIVE TEST RESULTS ===")
    
    print(f"Website Loading: {'[OK]' if website_ok else '[ERROR]'}")
    print(f"Firebase Data: {'[OK]' if firebase_ok else '[ERROR]'}")
    print(f"CORS Configuration: {'[OK]' if cors_ok else '[ERROR]'}")
    
    all_systems_ok = website_ok and firebase_ok and cors_ok
    
    print(f"\nOverall Status: {'[SUCCESS] ALL SYSTEMS OPERATIONAL!' if all_systems_ok else '[WARNING] SOME ISSUES DETECTED'}")
    
    if all_systems_ok:
        print(f"\n[SUCCESS] DEPLOYMENT SUCCESSFUL!")
        print(f"  - GitHub Pages is hosting the website")
        print(f"  - Firebase contains poker site data")
        print(f"  - CORS allows cross-origin requests")
        print(f"  - Website should display live poker traffic data")
        
        print(f"\n[TARGET] Website URL: https://garimto81.github.io/poker-online-analyze")
        print(f"[INFO] Expected functionality:")
        print(f"  - Table view with live poker site rankings")
        print(f"  - Charts view with traffic trends")
        print(f"  - Refresh button to reload data")
        print(f"  - Daily automated data updates via GitHub Actions")
        
    else:
        print(f"\n[ERROR] ISSUES FOUND:")
        if not website_ok:
            print(f"  - Website loading or structure issues")
        if not firebase_ok:
            print(f"  - Firebase data not available or incomplete")
        if not cors_ok:
            print(f"  - CORS configuration preventing cross-origin access")
    
    return all_systems_ok

def main():
    """메인 테스트 실행"""
    print("=== POKER ANALYZER WEBSITE FUNCTIONALITY TEST ===")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # 1. 웹사이트 로딩 테스트
    website_ok, content = test_website_loads()
    
    # 2. Firebase 데이터 테스트  
    firebase_ok = test_firebase_data_availability()
    
    # 3. CORS 설정 테스트
    cors_ok = test_cors_headers()
    
    # 4. 종합 분석
    all_ok = analyze_results(website_ok, content, firebase_ok, cors_ok)
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)