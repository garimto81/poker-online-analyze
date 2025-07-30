#!/usr/bin/env python3
"""
Firebase 데이터 구조 디버깅
실제 데이터가 어떻게 저장되어 있는지 확인
"""
import requests
import json
from datetime import datetime

def debug_firebase_structure():
    """Firebase 데이터 구조 분석"""
    print("=== FIREBASE DATA STRUCTURE DEBUG ===")
    
    project_id = 'poker-online-analyze'
    base_url = f'https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents'
    
    # 1. 전체 컬렉션 구조 확인
    print("\n[DEBUG] Checking root collections...")
    try:
        response = requests.get(base_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            print(f"Root response keys: {list(data.keys()) if isinstance(data, dict) else 'Not a dict'}")
            print(f"Response: {json.dumps(data, indent=2)[:500]}...")
    except Exception as e:
        print(f"Error checking root: {e}")
    
    # 2. sites 컬렉션 상세 분석
    print(f"\n[DEBUG] Analyzing sites collection...")
    sites_url = f"{base_url}/sites"
    
    try:
        response = requests.get(sites_url, timeout=30)
        if response.status_code == 200:
            data = response.json()
            
            if 'documents' in data and data['documents']:
                total_sites = len(data['documents'])
                print(f"Total sites: {total_sites}")
                
                # 첫 번째 사이트 구조 분석
                first_site = data['documents'][0]
                site_name = first_site['name'].split('/')[-1]
                print(f"\nSample site: {site_name}")
                print(f"Site fields: {list(first_site.get('fields', {}).keys())}")
                
                # 사이트 필드 상세 정보
                fields = first_site.get('fields', {})
                for field_name, field_data in fields.items():
                    field_type = list(field_data.keys())[0] if field_data else 'unknown'
                    field_value = list(field_data.values())[0] if field_data else 'unknown'
                    print(f"  {field_name}: {field_type} = {field_value}")
                
                # 3. traffic_logs 서브컬렉션 확인
                print(f"\n[DEBUG] Checking traffic_logs for {site_name}...")
                traffic_url = f"{base_url}/sites/{site_name}/traffic_logs"
                
                traffic_response = requests.get(traffic_url, timeout=30)
                print(f"Traffic logs status: {traffic_response.status_code}")
                
                if traffic_response.status_code == 200:
                    traffic_data = traffic_response.json()
                    print(f"Traffic response keys: {list(traffic_data.keys()) if isinstance(traffic_data, dict) else 'Not a dict'}")
                    
                    if 'documents' in traffic_data:
                        traffic_docs = traffic_data['documents']
                        print(f"Traffic logs count: {len(traffic_docs)}")
                        
                        if traffic_docs:
                            # 최신 traffic log 분석
                            latest_log = traffic_docs[0]
                            print(f"Latest log fields: {list(latest_log.get('fields', {}).keys())}")
                            
                            log_fields = latest_log.get('fields', {})
                            for field_name, field_data in log_fields.items():
                                field_type = list(field_data.keys())[0] if field_data else 'unknown'
                                field_value = list(field_data.values())[0] if field_data else 'unknown'
                                print(f"  {field_name}: {field_type} = {field_value}")
                    else:
                        print("No traffic_logs documents found")
                        print(f"Traffic response: {json.dumps(traffic_data, indent=2)[:300]}...")
                
                # 4. 다른 사이트도 몇 개 확인해보기
                print(f"\n[DEBUG] Checking other sites for traffic logs...")
                for i in range(1, min(5, total_sites)):  # 최대 4개 더 확인
                    site = data['documents'][i]
                    site_name = site['name'].split('/')[-1]
                    
                    traffic_url = f"{base_url}/sites/{site_name}/traffic_logs"
                    traffic_response = requests.get(traffic_url, timeout=10)
                    
                    if traffic_response.status_code == 200:
                        traffic_data = traffic_response.json()
                        traffic_count = len(traffic_data.get('documents', []))
                        print(f"  {site_name}: {traffic_count} traffic logs")
                    else:
                        print(f"  {site_name}: Error {traffic_response.status_code}")
            
            else:
                print("No sites documents found")
                print(f"Sites response: {json.dumps(data, indent=2)[:500]}...")
                
    except Exception as e:
        print(f"Error analyzing sites: {e}")

if __name__ == "__main__":
    debug_firebase_structure()