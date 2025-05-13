#!/usr/bin/env python3
"""
Simple script to test the LLM Query Understanding Service API.
"""
import requests
import json
import time
import sys

def test_parse_endpoint(url, query):
    """Test the /parse endpoint with a given query."""
    print(f"Testing with query: '{query}'")
    try:
        start_time = time.time()
        response = requests.post(
            f"{url}/parse", 
            json={"query": query}
        )
        elapsed = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ Success! Response received in {elapsed:.2f} seconds:")
            print(json.dumps(result, indent=2))
            return True
        else:
            print(f"\n❌ Error: Status code {response.status_code}")
            print(response.text)
            return False
    except Exception as e:
        print(f"\n❌ Error: {str(e)}")
        return False

if __name__ == "__main__":
    # Default values
    base_url = "http://localhost:8000"
    default_query = "I need a red wooden chair"
    
    # Use command line arguments if provided
    if len(sys.argv) > 1:
        base_url = sys.argv[1]
    
    query = default_query
    if len(sys.argv) > 2:
        query = sys.argv[2]
    
    # Run the test
    print(f"Testing API at {base_url}...")
    test_parse_endpoint(base_url, query)
