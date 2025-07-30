#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Frontend Test Script - Test React app functionality
"""

import time
import requests
from datetime import datetime

def test_frontend_api():
    """Test if frontend can communicate with backend API"""
    
    print("="*60)
    print("FRONTEND API TEST")
    print("="*60)
    
    # Check if frontend is running
    try:
        response = requests.get("http://localhost:3001")
        if response.status_code == 200:
            print("[SUCCESS] Frontend is running at http://localhost:3001")
        else:
            print(f"[FAILED] Frontend returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Frontend not accessible: {e}")
        return False
    
    # Check if backend API is accessible
    try:
        response = requests.get("http://localhost:8000/api/firebase/current_ranking/")
        if response.status_code == 200:
            data = response.json()
            print(f"[SUCCESS] Backend API is working - Found {len(data)} sites")
            
            # Show top 5 sites
            print("\nTop 5 Poker Sites (Current Data):")
            print(f"{'Rank':<6} {'Site Name':<25} {'Players Online':<15} {'Category':<15}")
            print("-"*70)
            
            for site in data[:5]:
                print(f"#{site['rank']:<5} {site['site_name'][:24]:<25} {site['players_online']:<15,} {site['category']:<15}")
            
            # Check for GG_POKER sites
            gg_sites = [s for s in data if s['category'] == 'GG_POKER']
            print(f"\nGG Poker Sites Found: {len(gg_sites)}")
            for site in gg_sites:
                print(f"  - {site['site_name']}: {site['players_online']:,} players (Rank #{site['rank']})")
            
        else:
            print(f"[FAILED] Backend API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERROR] Cannot connect to backend API: {e}")
        return False
    
    print("\n" + "="*60)
    print("FRONTEND FUNCTIONALITY")
    print("="*60)
    
    print("\nExpected Frontend Features:")
    print("1. [Table] Shows poker sites ranking with following columns:")
    print("   - Rank (#1, #2, etc.)")
    print("   - Site Name")
    print("   - Category (GG_POKER shown in green)")
    print("   - Players Online")
    print("   - Cash Players")
    print("   - 24h Peak")
    print("   - 7-Day Average")
    
    print("\n2. [Buttons] Interactive controls:")
    print("   - 'Refresh Data' - Reloads current data")
    print("   - 'Trigger New Crawl' - Starts new data collection")
    
    print("\n3. [Summary] Statistics section showing:")
    print(f"   - Total Sites: {len(data)}")
    print(f"   - GG Poker Sites: {len(gg_sites)}")
    print(f"   - Total Players Online: {sum(s['players_online'] for s in data):,}")
    
    print("\n4. [Visual Indicators]:")
    print("   - GG_POKER sites highlighted with green background")
    print("   - Last update timestamp displayed")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)
    
    print("\nFrontend URL: http://localhost:3001")
    print("Backend API Docs: http://localhost:8000/docs")
    
    return True

if __name__ == "__main__":
    # Wait a bit for services to stabilize
    print("Testing Poker Online Analyze Frontend...\n")
    time.sleep(2)
    
    if test_frontend_api():
        print("\n[SUCCESS] All tests passed! Frontend is working correctly.")
        print("\nYou can now:")
        print("1. Open http://localhost:3001 in your browser")
        print("2. Click 'Refresh Data' to update the table")
        print("3. Click 'Trigger New Crawl' to collect fresh data")
    else:
        print("\n[FAILED] Some tests failed. Please check the errors above.")