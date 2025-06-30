#!/usr/bin/env python3

import requests
import json

def test_search():
    print("=== Testing Search API ===")
    
    # Test simple search without authentication
    test_queries = ["python", "java", "web", "data"]
    
    for query in test_queries:
        print(f"\n🔍 Testing search for: '{query}'")
        try:
            response = requests.get(f"http://localhost:8000/search/all?query={query}")
            print(f"Status: {response.status_code}")
            
            if response.status_code == 200:
                results = response.json()
                print(f"✅ Found {len(results)} courses")
                if results:
                    print(f"   First result: {results[0]['title']}")
            else:
                print(f"❌ Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    test_search() 