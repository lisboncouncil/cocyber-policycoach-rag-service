#!/usr/bin/env python3
"""
Test script for streaming functionality
"""
import requests
import json
import time

def test_streaming_endpoint():
    """Test the /conversation/stream endpoint"""
    url = "http://localhost:5050/conversation/stream"
    
    data = {
        "message": "What is cybersecurity?",
        "sessionId": "test-session-123"
    }
    
    print("Testing streaming endpoint...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print("\nStreaming response:")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=data, stream=True)
        
        if response.status_code != 200:
            print(f"Error: {response.status_code}")
            print(response.text)
            return
        
        full_answer = ""
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    data_str = line[6:]  # Remove 'data: ' prefix
                    try:
                        chunk_data = json.loads(data_str)
                        
                        if chunk_data.get('done', False):
                            # Final chunk with complete response
                            print(f"\n\nFinal response received:")
                            print(f"Question: {chunk_data.get('question', 'N/A')}")
                            print(f"Answer: {chunk_data.get('answer', 'N/A')}")
                            print(f"Sources: {len(chunk_data.get('sources', []))}")
                            print(f"Session ID: {chunk_data.get('sessionId', 'N/A')}")
                            print(f"Metadata: {chunk_data.get('metadata', {})}")
                        else:
                            # Streaming chunk
                            chunk = chunk_data.get('chunk', '')
                            print(chunk, end='', flush=True)
                            full_answer += chunk
                    except json.JSONDecodeError as e:
                        print(f"Error parsing JSON: {e}")
                        print(f"Raw data: {data_str}")
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running on localhost:5050?")
    except Exception as e:
        print(f"Error: {e}")

def test_non_streaming_endpoint():
    """Test the regular /conversation endpoint for comparison"""
    url = "http://localhost:5050/conversation"
    
    data = {
        "message": "What is cybersecurity?",
        "sessionId": "test-session-456"
    }
    
    print("\n\nTesting non-streaming endpoint...")
    print(f"URL: {url}")
    print(f"Data: {data}")
    print("\nResponse:")
    print("-" * 50)
    
    try:
        response = requests.post(url, json=data)
        
        if response.status_code == 200:
            result = response.json()
            print(f"Question: {result.get('question', 'N/A')}")
            print(f"Answer: {result.get('answer', 'N/A')}")
            print(f"Sources: {len(result.get('sources', []))}")
            print(f"Session ID: {result.get('sessionId', 'N/A')}")
            print(f"Metadata: {result.get('metadata', {})}")
        else:
            print(f"Error: {response.status_code}")
            print(response.text)
    
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to server. Is it running on localhost:5050?")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    print("Streaming Implementation Test")
    print("=" * 50)
    
    # Test streaming endpoint
    test_streaming_endpoint()
    
    # Test non-streaming for comparison
    test_non_streaming_endpoint()
    
    print("\n\nTest completed!")