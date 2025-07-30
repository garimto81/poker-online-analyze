#!/usr/bin/env python3
"""
배포 테스트 및 문제 해결 스크립트
GitHub Pages와 Vercel API를 테스트합니다.
"""
import requests
import json
import time
from datetime import datetime

def test_api_endpoint(url, description, timeout=30):
    """API 엔드포인트 테스트"""
    print(f"\n[TEST] Testing {description}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, timeout=timeout)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print("[OK] JSON Response received")
                
                # 데이터 유형별 상세 분석
                if isinstance(data, dict):
                    if 'message' in data:
                        print(f"Message: {data['message']}")
                    if 'status' in data:
                        print(f"Status: {data['status']}")
                    if isinstance(data, dict) and len(data) > 0:
                        print(f"Keys: {list(data.keys())[:5]}...")  # 처음 5개 키만
                elif isinstance(data, list):
                    print(f"Array length: {len(data)}")
                    if len(data) > 0:
                        print(f"First item keys: {list(data[0].keys()) if isinstance(data[0], dict) else 'N/A'}")
                
                return True, data
            except json.JSONDecodeError:
                print("[ERROR] Invalid JSON response")
                print(f"Response text (first 200 chars): {response.text[:200]}")
                return False, None
        else:
            print(f"[ERROR] HTTP Error: {response.status_code}")
            print(f"Response: {response.text[:200]}")
            return False, None
            
    except requests.exceptions.ConnectionError:
        print("[ERROR] Connection Error - Server might be down")
        return False, None
    except requests.exceptions.Timeout:
        print("[ERROR] Timeout Error - Server is slow to respond")
        return False, None
    except Exception as e:
        print(f"[ERROR] Unexpected Error: {e}")
        return False, None

def test_vercel_api():
    """Vercel API 서버리스 함수 테스트"""
    print("=" * 60)
    print("=== TESTING VERCEL API SERVERLESS FUNCTIONS")
    print("=" * 60)
    
    base_url = "https://poker-analyzer-api.vercel.app"
    
    tests = [
        (f"{base_url}/", "Root endpoint"),
        (f"{base_url}/health", "Health check"),
        (f"{base_url}/test", "Test endpoint"),
        (f"{base_url}/api/firebase/current_ranking/", "Current ranking API"),
        (f"{base_url}/api/firebase/all_sites_daily_stats/", "All sites daily stats API")
    ]
    
    results = []
    for url, description in tests:
        success, data = test_api_endpoint(url, description)
        results.append((description, success, data))
        time.sleep(1)  # API 요청 간격
    
    return results

def test_github_pages():
    """GitHub Pages 웹사이트 테스트"""
    print("\n" + "=" * 60)
    print("=== TESTING GITHUB PAGES WEBSITE")
    print("=" * 60)
    
    github_pages_url = "https://garimto81.github.io/poker-online-analyze"
    
    print(f"\n[TEST] Testing GitHub Pages Website")
    print(f"URL: {github_pages_url}")
    
    try:
        response = requests.get(github_pages_url, timeout=30)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            print("[OK] Website is accessible")
            
            # HTML 내용 분석
            html_content = response.text
            if "Poker" in html_content and "React" in html_content:
                print("[OK] React app detected in HTML")
            if "root" in html_content:
                print("[OK] React root element found")
            
            print(f"Content length: {len(html_content)} characters")
            return True
        else:
            print(f"[ERROR] HTTP Error: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Error accessing GitHub Pages: {e}")
        return False

def analyze_results(api_results, pages_result):
    """테스트 결과 분석 및 권장사항"""
    print("\n" + "=" * 60)
    print("=== TEST RESULTS ANALYSIS ===")
    print("=" * 60)
    
    # API 결과 분석
    api_success_count = sum(1 for _, success, _ in api_results if success)
    total_api_tests = len(api_results)
    
    print(f"\nAPI Tests: {api_success_count}/{total_api_tests} passed")
    
    for description, success, data in api_results:
        status = "[OK]" if success else "[FAIL]"
        print(f"  {status} {description}")
    
    # GitHub Pages 결과
    pages_status = "[OK]" if pages_result else "[ERROR]"
    print(f"\nGitHub Pages: {pages_status} {'Accessible' if pages_result else 'Not accessible'}")
    
    # 전체 상태
    all_systems_ok = api_success_count == total_api_tests and pages_result
    
    print(f"\nOverall Status: {'[SUCCESS] ALL SYSTEMS GO!' if all_systems_ok else '[WARNING] ISSUES DETECTED'}")
    
    # 권장사항
    if not all_systems_ok:
        print("\nRECOMMENDED ACTIONS:")
        if api_success_count < total_api_tests:
            print("  - Check Vercel deployment status")
            print("  - Verify Firebase service account key in Vercel environment variables")
            print("  - Check Vercel function logs for errors")
        
        if not pages_result:
            print("  - Check GitHub Pages deployment status in Actions tab")
            print("  - Verify GitHub Pages is enabled in repository settings")
            print("  - Check for build errors in GitHub Actions logs")
    
    return all_systems_ok

def main():
    """메인 테스트 실행"""
    print("=== POKER ANALYZER DEPLOYMENT TEST ===")
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Vercel API 테스트
    api_results = test_vercel_api()
    
    # GitHub Pages 테스트
    pages_result = test_github_pages()
    
    # 결과 분석
    all_ok = analyze_results(api_results, pages_result)
    
    # 최종 보고
    print(f"\n{'=== DEPLOYMENT TEST COMPLETED SUCCESSFULLY! ===' if all_ok else '=== DEPLOYMENT ISSUES FOUND ==='}")
    print(f"Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return all_ok

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)