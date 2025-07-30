#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Firebase 연동 테스트 스크립트
"""

import os
import sys
import json
from datetime import datetime, timezone

# 현재 디렉토리를 Python 경로에 추가
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.poker_crawler import LivePokerScoutCrawler, upload_to_firestore_efficiently, db

def test_firebase_connection():
    """Firebase connection test"""
    print("=" * 60)
    print("Firebase Connection Test Started")
    print("=" * 60)
    
    # 1. Check Firebase connection
    if db is None:
        print("[FAILED] Firebase connection failed!")
        print("Please check if Firebase service account key file exists in one of these paths:")
        print("  - backend/key/firebase-service-account-key.json")
        print("  - key/firebase-service-account-key.json")
        return False
    else:
        print("[SUCCESS] Firebase connection successful!")
    
    # 2. 테스트 데이터 생성
    test_data = [{
        'site_name': 'TEST_SITE_' + datetime.now().strftime('%Y%m%d_%H%M%S'),
        'category': 'TEST',
        'players_online': 100,
        'cash_players': 50,
        'peak_24h': 150,
        'seven_day_avg': 120,
        'collected_at': datetime.now(timezone.utc).isoformat()
    }]
    
    print(f"\nTest data created: {test_data[0]['site_name']}")
    
    # 3. Firestore에 업로드
    try:
        upload_to_firestore_efficiently(test_data)
        print("[SUCCESS] Firestore upload successful!")
    except Exception as e:
        print(f"[FAILED] Firestore upload failed: {e}")
        return False
    
    # 4. 업로드된 데이터 확인
    try:
        site_ref = db.collection('sites').document(test_data[0]['site_name'])
        site_doc = site_ref.get()
        
        if site_doc.exists:
            print(f"[SUCCESS] Site document found: {site_doc.to_dict()}")
            
            # traffic_logs 확인
            traffic_logs = site_ref.collection('traffic_logs').limit(1).get()
            if traffic_logs:
                print(f"[SUCCESS] Traffic log found: {traffic_logs[0].to_dict()}")
            else:
                print("[FAILED] Traffic log not found.")
        else:
            print("[FAILED] Site document not found.")
            return False
    except Exception as e:
        print(f"[FAILED] Failed to read data: {e}")
        return False
    
    print("\n[SUCCESS] Firebase connection test completed!")
    return True

def test_crawler():
    """Crawler test"""
    print("\n" + "=" * 60)
    print("Crawler Test Started")
    print("=" * 60)
    
    crawler = LivePokerScoutCrawler()
    data = crawler.crawl_pokerscout_data()
    
    if data:
        print(f"[SUCCESS] Crawling successful! Found {len(data)} sites")
        print(f"\nTop 5 sites:")
        for i, site in enumerate(data[:5]):
            print(f"{i+1}. {site['site_name']} - {site['players_online']:,} players online")
        
        # Firebase에 저장할지 확인
        save = input("\nSave to Firebase? (y/n): ")
        if save.lower() == 'y':
            try:
                upload_to_firestore_efficiently(data)
                print("[SUCCESS] Firebase save completed!")
            except Exception as e:
                print(f"[FAILED] Firebase save failed: {e}")
    else:
        print("[FAILED] Crawling failed!")
    
    return bool(data)

if __name__ == "__main__":
    print("Poker Online Analyze - Firebase Connection Test\n")
    
    # Firebase 연결 테스트
    if test_firebase_connection():
        # 크롤러 테스트
        test_crawler()
    else:
        print("\n[WARNING] Firebase connection failed. Please check the service account key.")
        print("\nHow to create key file:")
        print("1. Go to Firebase Console (https://console.firebase.google.com)")
        print("2. Project Settings > Service Accounts > Generate New Private Key")
        print("3. Save the downloaded JSON file as backend/key/firebase-service-account-key.json")