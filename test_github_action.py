#!/usr/bin/env python3
"""
GitHub Actions 크롤링 테스트 및 문제 자동 해결 스크립트
"""
import os
import sys
import json
import time
import subprocess

def test_firebase_key():
    """Firebase 키 파일 테스트"""
    print("1. Checking Firebase key file...")
    key_path = "backend/key/firebase-service-account-key.json"
    
    if not os.path.exists(key_path):
        print("[ERROR] Firebase key file not found!")
        return False
    
    try:
        with open(key_path, 'r', encoding='utf-8') as f:
            key_data = json.load(f)
            required_fields = ['type', 'project_id', 'private_key_id', 'private_key']
            
            for field in required_fields:
                if field not in key_data:
                    print(f"[ERROR] Firebase key missing '{field}' field!")
                    return False
            
            print("[OK] Firebase key file is valid")
            return True
    except Exception as e:
        print(f"[ERROR] Firebase key file read error: {e}")
        return False

def test_crawler_locally():
    """로컬에서 크롤러 테스트"""
    print("\n2. Testing local crawler...")
    
    # Python 경로 확인
    python_cmd = sys.executable
    
    # 크롤러 테스트 코드
    test_code = """
import sys
sys.path.append('backend')
try:
    from app.services.poker_crawler import LivePokerScoutCrawler
    crawler = LivePokerScoutCrawler()
    print("[OK] Crawler import success")
    
    # 간단한 테스트 크롤링
    import requests
    from bs4 import BeautifulSoup
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    response = requests.get('https://www.pokerscout.com', headers=headers, timeout=10)
    if response.status_code == 200:
        print("[OK] PokerScout connection success")
    else:
        print(f"[ERROR] PokerScout connection failed: {response.status_code}")
        
except Exception as e:
    print(f"[ERROR] Crawler test failed: {e}")
    sys.exit(1)
"""
    
    try:
        result = subprocess.run(
            [python_cmd, '-c', test_code],
            capture_output=True,
            text=True,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        
        print(result.stdout)
        if result.stderr:
            print(f"Warning: {result.stderr}")
            
        return result.returncode == 0
    except Exception as e:
        print(f"[ERROR] Local test failed: {e}")
        return False

def check_github_secrets():
    """GitHub Secrets 설정 안내"""
    print("\n3. GitHub Secrets setup check")
    print("Please manually verify the following steps:")
    print("1. https://github.com/garimto81/poker-online-analyze/settings/secrets/actions")
    print("2. Check if FIREBASE_SERVICE_ACCOUNT_KEY is set")
    print("3. If not, add it via 'New repository secret'")
    
    key_path = "backend/key/firebase-service-account-key.json"
    if os.path.exists(key_path):
        print(f"\nKey file location: {os.path.abspath(key_path)}")
        print("Copy the entire contents of this file and paste into GitHub Secret.")
    
    return True

def create_test_workflow():
    """테스트용 간단한 워크플로우 생성"""
    print("\n4. Creating test workflow...")
    
    test_workflow = """name: Test Crawler Setup

on:
  workflow_dispatch:
  push:
    branches: [ main ]
    paths:
      - '.github/workflows/test-crawler.yml'

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - name: Checkout
      uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    
    - name: Test Python imports
      run: |
        python -c "print('Python 버전:', sys.version)" || true
        python -c "import sys; print('Python 경로:', sys.executable)" || true
    
    - name: Install basic requirements
      run: |
        pip install requests beautifulsoup4 cloudscraper
        pip list
    
    - name: Test crawler import
      run: |
        cd backend
        python -c "
        try:
            import sys
            sys.path.append('.')
            from app.services.poker_crawler import LivePokerScoutCrawler
            print('[OK] Crawler import success!')
        except ImportError as e:
            print(f'[ERROR] Import failed: {e}')
            print('현재 디렉토리:', os.getcwd())
            print('sys.path:', sys.path)
            import os
            print('파일 목록:', os.listdir('.'))
        "
    
    - name: Test network access
      run: |
        curl -I https://www.pokerscout.com || echo "PokerScout 접속 테스트"
"""
    
    workflow_path = ".github/workflows/test-crawler.yml"
    os.makedirs(os.path.dirname(workflow_path), exist_ok=True)
    
    with open(workflow_path, 'w', encoding='utf-8') as f:
        f.write(test_workflow)
    
    print(f"[OK] Test workflow created: {workflow_path}")
    return True

def main():
    """메인 테스트 함수"""
    print("=== GitHub Actions Crawling Auto Test Start ===\n")
    
    # 1. Firebase 키 테스트
    if not test_firebase_key():
        print("\nSolution:")
        print("1. Download service account key from Firebase Console")
        print("2. Save as backend/key/firebase-service-account-key.json")
        print("\nContinuing without Firebase key for GitHub Actions test...")
    
    # 2. 로컬 크롤러 테스트
    if not test_crawler_locally():
        print("\nSolution:")
        print("1. pip install -r backend/requirements.txt 실행")
        print("2. Check Python path")
        return False
    
    # 3. GitHub Secrets 안내
    check_github_secrets()
    
    # 4. 테스트 워크플로우 생성
    create_test_workflow()
    
    print("\n=== Test Complete ===")
    print("\nNext steps:")
    print("1. git add .github/workflows/test-crawler.yml")
    print("2. git commit -m 'Add test workflow'")
    print("3. git push origin main")
    print("4. Check results in GitHub Actions tab")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)