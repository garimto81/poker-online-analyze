#!/usr/bin/env python3
import requests

def check_html_content():
    print("Checking HTML content...")
    try:
        r = requests.get('https://garimto81.github.io/poker-online-analyze')
        content = r.content.decode('utf-8', errors='ignore')
        
        # Extract first 2000 characters
        print("HTML Content (first 2000 chars):")
        print("=" * 50)
        print(content[:2000])
        print("=" * 50)
        
        # Look for specific patterns
        print("\nPattern Analysis:")
        patterns = {
            'HTML5 doctype': '<!DOCTYPE html>' in content,
            'Title tag': '<title>' in content,
            'Root div': 'id="root"' in content,
            'React bundle': any(x in content for x in ['react', 'React', '/static/js/', 'bundle']),
            'CSS links': '<link' in content and '.css' in content,
            'Script tags': '<script' in content,
        }
        
        for pattern, found in patterns.items():
            print(f"  {pattern}: {'YES' if found else 'NO'}")
        
        return content
        
    except Exception as e:
        print(f"Error: {e}")
        return None

if __name__ == "__main__":
    check_html_content()