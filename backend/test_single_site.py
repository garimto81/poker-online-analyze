#!/usr/bin/env python3
"""
단일 사이트로 문서 ID 형식 테스트
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime, timezone
import requests
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FIREBASE_PROJECT_ID = "poker-online-analyze"
FIRESTORE_BASE_URL = f"https://firestore.googleapis.com/v1/projects/{FIREBASE_PROJECT_ID}/databases/(default)/documents"

# 테스트 데이터
test_data = {
    'site_name': 'TestSite123',
    'category': 'TEST',
    'players_online': 12345,
    'cash_players': 6789,
    'peak_24h': 15000,
    'seven_day_avg': 10000,
    'collected_at': datetime.now(timezone.utc).isoformat()
}

logger.info(f"테스트 데이터 collected_at: {test_data['collected_at']}")

# traffic_logs에 추가
doc_id = test_data['collected_at']
traffic_url = f"{FIRESTORE_BASE_URL}/sites/{test_data['site_name']}/traffic_logs/{doc_id}"

traffic_doc = {
    "fields": {
        "players_online": {"integerValue": str(test_data['players_online'])},
        "cash_players": {"integerValue": str(test_data['cash_players'])},
        "peak_24h": {"integerValue": str(test_data['peak_24h'])},
        "seven_day_avg": {"integerValue": str(test_data['seven_day_avg'])},
        "collected_at": {"timestampValue": test_data['collected_at']}
    }
}

# PATCH 요청으로 문서 생성
response = requests.patch(traffic_url, json=traffic_doc, headers={'Content-Type': 'application/json'})

logger.info(f"응답 상태: {response.status_code}")
if response.status_code in [200, 201]:
    logger.info("성공! 문서가 올바른 ID로 생성되었습니다.")
    logger.info(f"문서 ID: {doc_id}")
else:
    logger.error(f"실패: {response.text}")

# 생성된 문서 확인
logger.info("\n생성된 문서 확인:")
get_response = requests.get(traffic_url)
if get_response.status_code == 200:
    import json
    doc = get_response.json()
    logger.info(f"문서 경로: {doc.get('name', '')}")
    logger.info(f"문서 ID: {doc.get('name', '').split('/')[-1]}")