#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Quick API Test - Run server and test endpoints
"""

import subprocess
import time
import requests
import threading
import os
import sys

def run_server():
    """Run the FastAPI server"""
    print("[SERVER] Starting FastAPI server...")
    # Change to backend directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    subprocess.run([sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"])

def test_api():
    """Test API endpoints"""
    print("[TEST] Waiting for server to start...")
    time.sleep(5)  # Wait for server to start
    
    api_base = "http://localhost:8000"
    
    print("\n" + "="*60)
    print("API ENDPOINT TESTS")
    print("="*60)
    
    # Test 1: Root endpoint
    try:
        print("\n1. Testing root endpoint...")
        response = requests.get(f"{api_base}/")
        if response.status_code == 200:
            print(f"[SUCCESS] Root endpoint: {response.json()}")
        else:
            print(f"[FAILED] Root endpoint: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Root endpoint: {e}")
    
    # Test 2: Firebase sites endpoint
    try:
        print("\n2. Testing Firebase sites endpoint...")
        response = requests.get(f"{api_base}/api/firebase/sites/")
        if response.status_code == 200:
            sites = response.json()
            print(f"[SUCCESS] Found {len(sites)} sites")
            if sites:
                print(f"   First site: {sites[0].get('site_name', 'Unknown')}")
        else:
            print(f"[FAILED] Sites endpoint: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Sites endpoint: {e}")
    
    # Test 3: Current ranking endpoint
    try:
        print("\n3. Testing current ranking endpoint...")
        response = requests.get(f"{api_base}/api/firebase/current_ranking/")
        if response.status_code == 200:
            ranking = response.json()
            print(f"[SUCCESS] Current ranking with {len(ranking)} sites")
            if ranking:
                print("\n   Top 3 sites:")
                for site in ranking[:3]:
                    print(f"   #{site['rank']} {site['site_name']} - {site['players_online']:,} players")
        else:
            print(f"[FAILED] Ranking endpoint: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] Ranking endpoint: {e}")
    
    # Test 4: API documentation
    try:
        print("\n4. Testing API documentation...")
        response = requests.get(f"{api_base}/docs")
        if response.status_code == 200:
            print(f"[SUCCESS] API docs available at: {api_base}/docs")
        else:
            print(f"[FAILED] API docs: {response.status_code}")
    except Exception as e:
        print(f"[ERROR] API docs: {e}")
    
    print("\n" + "="*60)
    print("API TESTS COMPLETED")
    print("="*60)
    print(f"\nYou can now:")
    print(f"1. View API docs at: {api_base}/docs")
    print(f"2. Test frontend at: http://localhost:3000")
    print(f"3. Keep this server running for frontend testing")
    print(f"\nPress Ctrl+C to stop the server")

if __name__ == "__main__":
    # Start server in a thread
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    
    # Run tests
    test_api()
    
    # Keep the main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down...")
        sys.exit(0)