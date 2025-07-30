#!/usr/bin/env python3
import requests
import json

def test_website():
    print("Testing website...")
    try:
        r = requests.get('https://garimto81.github.io/poker-online-analyze')
        print(f"Status: {r.status_code}")
        print(f"Content length: {len(r.content)} bytes")
        
        # Convert to text safely
        try:
            content = r.content.decode('utf-8', errors='ignore')
            print(f"Text length: {len(content)} chars")
            
            # Look for key indicators
            has_root = 'id="root"' in content
            has_react = 'react' in content.lower()
            has_poker = 'poker' in content.lower()
            has_js = '.js' in content
            
            print(f"Has root div: {has_root}")
            print(f"Has React: {has_react}")
            print(f"Has Poker: {has_poker}")
            print(f"Has JS: {has_js}")
            
            return r.status_code == 200 and (has_root or has_react)
            
        except Exception as e:
            print(f"Content decode error: {e}")
            return r.status_code == 200
            
    except Exception as e:
        print(f"Request error: {e}")
        return False

def test_firebase():
    print("\nTesting Firebase...")
    try:
        url = 'https://firestore.googleapis.com/v1/projects/poker-online-analyze/databases/(default)/documents/sites'
        r = requests.get(url)
        print(f"Status: {r.status_code}")
        
        if r.status_code == 200:
            data = r.json()
            count = len(data.get('documents', []))
            print(f"Sites found: {count}")
            return count > 0
        return False
        
    except Exception as e:
        print(f"Firebase error: {e}")
        return False

if __name__ == "__main__":
    website_ok = test_website()
    firebase_ok = test_firebase()
    
    print(f"\n=== RESULTS ===")
    print(f"Website: {'OK' if website_ok else 'ERROR'}")
    print(f"Firebase: {'OK' if firebase_ok else 'ERROR'}")
    
    if website_ok and firebase_ok:
        print("\n[SUCCESS] All systems operational!")
        print("Website: https://garimto81.github.io/poker-online-analyze")
    else:
        print(f"\n[WARNING] Some issues detected")