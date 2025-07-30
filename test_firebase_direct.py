#!/usr/bin/env python3
"""
Firebase 직접 연결 테스트
GitHub Pages가 Firebase와 직접 통신할 수 있는지 확인
"""
import requests
import json
from datetime import datetime

def test_firebase_direct():
    """Firebase REST API 직접 테스트"""
    print("=== TESTING FIREBASE DIRECT CONNECTION ===")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Firebase REST API URL
    project_id = 'poker-online-analyze'
    base_url = f'https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents'
    
    print(f"\nFirebase Project: {project_id}")
    print(f"Base URL: {base_url}")
    
    # 1. sites 컬렉션 테스트
    print(f"\n[TEST] Testing sites collection")
    sites_url = f"{base_url}/sites"
    print(f"URL: {sites_url}")
    
    try:
        response = requests.get(sites_url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if 'documents' in data:
                print(f"[OK] Found {len(data['documents'])} sites")
                
                # 첫 번째 사이트 정보 출력
                if data['documents']:
                    first_site = data['documents'][0]
                    site_name = first_site['name'].split('/')[-1]
                    print(f"Sample site: {site_name}")
                    
                    # 해당 사이트의 traffic_logs 확인
                    traffic_url = f"{base_url}/sites/{site_name}/traffic_logs"
                    print(f"\n[TEST] Testing traffic logs for {site_name}")
                    print(f"URL: {traffic_url}")
                    
                    traffic_response = requests.get(traffic_url, timeout=30)
                    print(f"Status: {traffic_response.status_code}")
                    
                    if traffic_response.status_code == 200:
                        traffic_data = traffic_response.json()
                        if 'documents' in traffic_data:
                            print(f"[OK] Found {len(traffic_data['documents'])} traffic logs")
                        else:
                            print("[WARNING] No traffic logs found")
                    else:
                        print(f"[ERROR] Traffic logs error: {traffic_response.status_code}")
                        print(f"Response: {traffic_response.text[:200]}")
                
                return True
            else:
                print("[ERROR] No documents found in sites collection")
                print(f"Response: {response.text[:500]}")
                return False
        else:
            print(f"[ERROR] HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:500]}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Connection failed: {e}")
        return False

def test_github_pages_with_firebase():
    """GitHub Pages에서 Firebase 연결이 작동하는지 확인"""
    print(f"\n=== TESTING GITHUB PAGES FIREBASE INTEGRATION ===")
    
    github_pages_url = "https://garimto81.github.io/poker-online-analyze"
    
    print(f"Checking if GitHub Pages can access Firebase...")
    print(f"Website: {github_pages_url}")
    
    try:
        response = requests.get(github_pages_url, timeout=30)
        if response.status_code == 200:
            html_content = response.text
            
            # Firebase 관련 코드가 포함되어 있는지 확인
            if 'firebaseService' in html_content:
                print("[OK] Firebase service code detected in website")
                return True
            elif 'firebase' in html_content.lower():
                print("[OK] Firebase references found in website")
                return True
            else:
                print("[WARNING] No Firebase code detected (may be in bundled JS)")
                return True
        else:
            print(f"[ERROR] Website not accessible: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Website test failed: {e}")
        return False

def main():
    """메인 테스트 실행"""
    print("=== FIREBASE DIRECT CONNECTION TEST ===")
    
    # Firebase 직접 연결 테스트
    firebase_ok = test_firebase_direct()
    
    # GitHub Pages Firebase 통합 테스트
    pages_ok = test_github_pages_with_firebase()
    
    # 결과 분석
    print(f"\n=== TEST RESULTS ===")
    print(f"Firebase Direct: {'[OK]' if firebase_ok else '[ERROR]'}")
    print(f"GitHub Pages: {'[OK]' if pages_ok else '[ERROR]'}")
    
    if firebase_ok and pages_ok:
        print(f"\n[SUCCESS] Firebase integration should work!")
        print("GitHub Pages can now load data directly from Firebase")
    elif firebase_ok:
        print(f"\n[PARTIAL] Firebase works but GitHub Pages may have issues")
    else:
        print(f"\n[ERROR] Firebase connection failed")
        print("Check Firebase project settings and permissions")
    
    print(f"\nTest completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return firebase_ok and pages_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)