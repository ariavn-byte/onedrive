#!/usr/bin/env python3
"""
Test script for OneDrive Organizer MCP Server
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health check endpoint"""
    print("🔍 Testing health check...")
    try:
        response = requests.get(f"{BASE_URL}/health")
        if response.status_code == 200:
            print("✅ Health check passed")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Could not connect to server. Is it running?")
        return False

def test_tools_list():
    """Test tools listing endpoint"""
    print("🔍 Testing tools list...")
    try:
        response = requests.get(f"{BASE_URL}/tools")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Tools list: {data['tools']}")
            return True
        else:
            print(f"❌ Tools list failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Tools list error: {e}")
        return False

def test_tool_invocation():
    """Test tool invocation endpoint"""
    print("🔍 Testing tool invocation...")
    try:
        # Test with list_files tool
        data = {"folder_path": "/", "limit": 10}
        response = requests.post(f"{BASE_URL}/invoke/list_files", json=data)
        
        if response.status_code == 200:
            result = response.json()
            if result.get("success"):
                print("✅ Tool invocation successful")
                return True
            else:
                print(f"❌ Tool execution failed: {result.get('error')}")
                return False
        else:
            print(f"❌ Tool invocation failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Tool invocation error: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing OneDrive Organizer MCP Server...")
    print("=" * 50)
    
    tests = [
        test_health,
        test_tools_list,
        test_tool_invocation
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
        print()
    
    print("=" * 50)
    print(f"📊 Test Results: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Your server is working correctly.")
    else:
        print("⚠️  Some tests failed. Check your configuration and server status.")

if __name__ == "__main__":
    main()
