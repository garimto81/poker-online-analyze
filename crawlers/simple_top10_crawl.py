#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
간단한 상위 10개 크롤링 (이모지 없음)
"""

import cloudscraper
from bs4 import BeautifulSoup
from datetime import datetime
import json

def crawl_simple_top10():
    """간단한 상위 10개 크롤링"""
    print("수정된 로직으로 PokerScout 상위 10개 크롤링")
    print("=" * 60)
    
    scraper = cloudscraper.create_scraper()
    
    start_time = datetime.now()
    print(f"크롤링 시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    response = scraper.get('https://www.pokerscout.com', timeout=30)
    soup = BeautifulSoup(response.content, 'html.parser')
    table = soup.find('table', {'class': 'rankTable'})
    
    rows = table.find_all('tr')[1:]  # 헤더 제외
    collected_data = []
    
    for i, row in enumerate(rows):
        try:
            # 광고 행 건너뛰기
            if 'cus_top_traffic_coin' in row.get('class', []):
                continue
            
            brand_title = row.find('span', {'class': 'brand-title'})
            if not brand_title:
                continue
            
            site_name = brand_title.get_text(strip=True)
            if not site_name or len(site_name) < 2:
                continue
            
            # Players Online
            online_td = row.find('td', {'id': 'online'})
            players_online = 0
            if online_td:
                online_span = online_td.find('span')
                if online_span:
                    online_text = online_span.get_text(strip=True).replace(',', '')
                    if online_text.isdigit():
                        players_online = int(online_text)
            
            # Cash Players
            cash_players = 0
            cash_td = row.find('td', {'id': 'cash'})
            if cash_td:
                cash_text = cash_td.get_text(strip=True).replace(',', '')
                if cash_text.isdigit():
                    cash_players = int(cash_text)
            
            site_data = {
                'rank': len(collected_data) + 1,
                'site_name': site_name,
                'players_online': players_online,
                'cash_players': cash_players
            }
            
            collected_data.append(site_data)
            
            # 상위 10개까지만
            if len(collected_data) >= 10:
                break
                
        except Exception as e:
            continue
    
    return collected_data

# 실행
data = crawl_simple_top10()

print("\n상위 10개 포커 사이트 (수정된 로직)")
print("=" * 50)
print(f"{'순위':<4} {'사이트명':<25} {'온라인':<12} {'캐시':<8}")
print("-" * 50)

for site in data:
    print(f"{site['rank']:<4} {site['site_name']:<25} {site['players_online']:>8,}명 {site['cash_players']:>6,}명")

total_online = sum(site['players_online'] for site in data)
print("-" * 50)
print(f"총 온라인 플레이어: {total_online:,}명")

# GGNetwork 확인
gg_site = next((s for s in data if 'GGNetwork' in s['site_name']), None)
if gg_site:
    print(f"\nGGNetwork 확인:")
    print(f"  순위: {gg_site['rank']}위")
    print(f"  플레이어: {gg_site['players_online']:,}명")

print(f"\n크롤링 시점: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")