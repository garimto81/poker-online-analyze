#!/usr/bin/env python3
"""
GitHub에 데이터를 JSON 파일로 저장하는 스크립트
Firebase 대신 GitHub를 데이터 저장소로 사용
"""
import json
import requests
from datetime import datetime, timezone
import os

def save_data_to_github(data, github_token=None):
    """GitHub 저장소에 데이터를 JSON 파일로 저장"""
    
    # GitHub API 설정
    owner = "garimto81"
    repo = "poker-online-analyze"
    branch = "main"
    
    # 파일 경로 설정 (public 폴더에 저장하여 GitHub Pages에서 접근 가능)
    file_path = "frontend/public/data/latest.json"
    
    # 데이터 준비
    json_data = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "date": datetime.now().strftime("%Y-%m-%d"),
        "sites": data,
        "summary": {
            "totalSites": len(data),
            "totalCashPlayers": sum(s.get('cash_players', 0) for s in data),
            "totalOnlinePlayers": sum(s.get('players_online', 0) for s in data),
            "ggNetworkSites": len([s for s in data if s.get('category') == 'GG_POKER']),
            "ggNetworkPlayers": sum(s.get('cash_players', 0) for s in data if s.get('category') == 'GG_POKER')
        }
    }
    
    # JSON 파일 내용
    content = json.dumps(json_data, ensure_ascii=False, indent=2)
    
    if github_token:
        # GitHub API를 통해 업로드
        api_url = f"https://api.github.com/repos/{owner}/{repo}/contents/{file_path}"
        
        headers = {
            "Authorization": f"token {github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # 기존 파일 SHA 가져오기
        response = requests.get(api_url, headers=headers)
        sha = None
        if response.status_code == 200:
            sha = response.json()["sha"]
        
        # 파일 업데이트
        import base64
        data = {
            "message": f"Update poker data - {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "content": base64.b64encode(content.encode()).decode(),
            "branch": branch
        }
        
        if sha:
            data["sha"] = sha
        
        response = requests.put(api_url, json=data, headers=headers)
        
        if response.status_code in [200, 201]:
            print(f"✅ Successfully saved to GitHub: {file_path}")
            return True
        else:
            print(f"❌ Failed to save to GitHub: {response.status_code}")
            print(response.text)
            return False
    else:
        # 로컬 파일로 저장
        os.makedirs("frontend/public/data", exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Saved locally: {file_path}")
        return True

if __name__ == "__main__":
    # 테스트 데이터
    test_data = [
        {
            'site_name': 'WPT Global',
            'category': 'WPT',
            'rank': 1,
            'players_online': 5219,
            'cash_players': 1694,
            'peak_24h': 3825,
            'seven_day_avg': 2400
        }
    ]
    
    save_data_to_github(test_data)