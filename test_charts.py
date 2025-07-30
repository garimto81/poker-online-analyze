#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Charts Functionality
"""

import time
import requests
import json

def test_charts_api():
    """Test the new charts API endpoint"""
    
    print("="*60)
    print("TESTING CHARTS API")
    print("="*60)
    
    # Wait for server to be ready
    print("\nWaiting for servers to start...")
    time.sleep(5)
    
    # Test backend API
    api_url = "http://localhost:8001/api/firebase/top10_daily_stats/?days=7"
    
    try:
        print(f"\nTesting API: {api_url}")
        response = requests.get(api_url)
        
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] API returned data for {len(data['top10_sites'])} sites")
            print(f"Total players online: {data['total_players_online']:,}")
            print(f"Data period: {data['days']} days")
            
            print("\nTop 10 Sites with Market Share:")
            print(f"{'Rank':<5} {'Site Name':<25} {'Players':<12} {'Market Share':<12}")
            print("-"*60)
            
            # Sort sites by players online
            sorted_sites = sorted(
                [(name, info) for name, info in data['data'].items()],
                key=lambda x: x[1]['current_stats']['players_online'],
                reverse=True
            )
            
            for i, (site_name, site_info) in enumerate(sorted_sites):
                stats = site_info['current_stats']
                share = site_info['market_share']
                print(f"{i+1:<5} {site_name[:24]:<25} {stats['players_online']:<12,} {share:<12}%")
            
            # Check data availability
            print("\nData Points Available:")
            for site_name, site_info in list(data['data'].items())[:3]:  # Show first 3
                points = len(site_info['daily_data'])
                print(f"  - {site_name}: {points} data points")
            
            return True
            
        else:
            print(f"[FAILED] API returned status code: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"[ERROR] Failed to connect to API: {e}")
        return False

def test_frontend_charts():
    """Check if frontend is ready for charts"""
    
    print("\n" + "="*60)
    print("FRONTEND CHARTS FUNCTIONALITY")
    print("="*60)
    
    try:
        response = requests.get("http://localhost:3001")
        if response.status_code == 200:
            print("[SUCCESS] Frontend is running at http://localhost:3001")
            
            print("\nExpected Chart Features:")
            print("1. [Tab Navigation]")
            print("   - 'Table View' tab - Shows ranking table (default)")
            print("   - 'Charts View' tab - Shows charts and graphs")
            
            print("\n2. [Market Share Chart]")
            print("   - Pie chart showing market share of top 10 sites")
            print("   - Percentage and player count for each site")
            print("   - 'Others' category for remaining sites")
            
            print("\n3. [Trend Line Charts]")
            print("   - Players Online - Daily trend for top 10 sites")
            print("   - Cash Players - Daily trend for top 10 sites")
            print("   - 24h Peak - Daily trend for top 10 sites")
            print("   - 7-Day Average - Daily trend for top 10 sites")
            
            print("\n4. [Chart Features]")
            print("   - Interactive legends (click to hide/show lines)")
            print("   - Hover tooltips with exact values")
            print("   - Each site has unique color")
            print("   - Market share % shown in legend")
            
            return True
        else:
            print(f"[FAILED] Frontend returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Cannot connect to frontend: {e}")
        print("Make sure to run: cd frontend && npm start")
        return False

if __name__ == "__main__":
    print("Poker Online Analyze - Charts Feature Test\n")
    
    # Test API first
    if test_charts_api():
        # Then test frontend
        if test_frontend_charts():
            print("\n" + "="*60)
            print("ALL TESTS PASSED!")
            print("="*60)
            print("\nYou can now:")
            print("1. Open http://localhost:3001 in your browser")
            print("2. Click on 'Charts View' tab")
            print("3. View market share pie chart")
            print("4. Scroll down to see 4 trend line charts")
            print("5. Hover over charts for detailed information")
        else:
            print("\n[WARNING] Frontend test failed")
    else:
        print("\n[ERROR] API test failed. Make sure backend is running:")
        print("cd backend && uvicorn main:app --reload")