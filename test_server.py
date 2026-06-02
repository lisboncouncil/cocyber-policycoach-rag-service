#!/usr/bin/env python3
"""
Simple test client for the RAG conversation server.
Sends a greeting message and displays the response.
"""

import requests
import json
import argparse
import sys


def test_server(server_url, message="Hello, how are you?"):
    """Test the server with a simple message."""
    try:
        # Prepare the request
        url = f"{server_url}/conversation"
        payload = {
            "message": message
        }
        headers = {
            "Content-Type": "application/json"
        }
        
        # Send the request
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        # Return exact JSON response from server
        if response.status_code == 200:
            result = response.json()
            print(json.dumps(result, indent=2))
        else:
            # Return error in JSON format
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                error_response = {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text
                }
                print(json.dumps(error_response, indent=2))
                
    except requests.exceptions.ConnectionError:
        error_response = {
            "error": "Connection Error",
            "message": f"Could not connect to {server_url}"
        }
        print(json.dumps(error_response, indent=2))
    except requests.exceptions.Timeout:
        error_response = {
            "error": "Timeout Error", 
            "message": "Server took too long to respond"
        }
        print(json.dumps(error_response, indent=2))
    except requests.exceptions.RequestException as e:
        error_response = {
            "error": "Request Error",
            "message": str(e)
        }
        print(json.dumps(error_response, indent=2))
    except Exception as e:
        error_response = {
            "error": "Unexpected Error",
            "message": str(e)
        }
        print(json.dumps(error_response, indent=2))


def test_health(server_url):
    """Test the health endpoint."""
    try:
        url = f"{server_url}/health"
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            health_data = response.json()
            print(json.dumps(health_data, indent=2))
            return True
        else:
            try:
                error_data = response.json()
                print(json.dumps(error_data, indent=2))
            except:
                error_response = {
                    "error": f"HTTP {response.status_code}",
                    "response_text": response.text
                }
                print(json.dumps(error_response, indent=2))
            return False
            
    except Exception as e:
        error_response = {
            "error": "Health check error",
            "message": str(e)
        }
        print(json.dumps(error_response, indent=2))
        return False


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description="Test client for RAG conversation server - returns JSON responses",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Test localhost:5050
  %(prog)s --server http://localhost:8080     # Test custom server
  %(prog)s --message "What is cybersecurity?" # Custom message
  %(prog)s --health-only                      # Only test health endpoint
        """
    )
    
    parser.add_argument('--server', '-s', type=str, default='http://localhost:5050',
                       help='Server URL (default: http://localhost:5050)')
    parser.add_argument('--message', '-m', type=str, default='Hello, how are you?',
                       help='Message to send (default: "Hello, how are you?")')
    parser.add_argument('--health-only', action='store_true',
                       help='Only test the health endpoint')
    
    args = parser.parse_args()
    
    # Remove trailing slash from server URL
    server_url = args.server.rstrip('/')
    
    if args.health_only:
        test_health(server_url)
    else:
        # Test conversation endpoint
        test_server(server_url, args.message)


if __name__ == '__main__':
    main()