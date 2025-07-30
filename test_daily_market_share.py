#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Daily Market Share Calculation
"""

import requests
import json
from datetime import datetime

def test_daily_market_share():
    """Test if daily market share is calculated correctly"""
    
    print("="*60)
    print("DAILY MARKET SHARE TEST")
    print("="*60)
    
    # API 호출
    url = "http://localhost:8001/api/firebase/top10_daily_stats/?days=7"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n[SUCCESS] API returned data for {len(data['top10_sites'])} sites")
        
        # 첫 3개 사이트의 데이터 확인
        for i, site_name in enumerate(data['top10_sites'][:3]):
            site_data = data['data'][site_name]
            print(f"\n{i+1}. {site_name}")
            print(f"   Current market share: {site_data['market_share']}%")
            print(f"   Daily data points: {len(site_data['daily_data'])}")
            
            # 일별 데이터 확인
            if site_data['daily_data']:
                print("   Daily breakdown:")
                for day_data in site_data['daily_data']:
                    date = day_data['date'][:10]
                    players = day_data['players_online']
                    market_share = day_data.get('market_share', 'NOT CALCULATED')
                    print(f"     {date}: {players:,} players ({market_share}%)")
        
        # 데이터 구조 확인
        if data['data']:
            first_site = list(data['data'].keys())[0]
            if data['data'][first_site]['daily_data']:
                first_day = data['data'][first_site]['daily_data'][0]
                print(f"\nDaily data structure keys: {list(first_day.keys())}")
                
                if 'market_share' in first_day:
                    print("[PASS] Daily market share is being calculated!")
                else:
                    print("[FAIL] Daily market share is NOT being calculated")
                    print("      The API needs to be restarted or the code needs fixing")
    
    else:
        print(f"[ERROR] API returned status code: {response.status_code}")
        print(f"Response: {response.text}")

if __name__ == "__main__":
    test_daily_market_share()