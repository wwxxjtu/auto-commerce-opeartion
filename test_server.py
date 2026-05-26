import requests
import json
from datetime import datetime

WEBHOOK_URL = "http://localhost:8000/webhook/sms"
API_BASE = "http://localhost:8000/api"


def test_webhook():
    print("Testing webhook endpoint...")
    
    test_data = {
        "sender": "10086",
        "content": f"测试短信 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "sim_slot": "SIM1",
        "device_name": "TestPhone"
    }
    
    try:
        response = requests.post(WEBHOOK_URL, json=test_data)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_get_all_sms():
    print("\nTesting get all SMS...")
    
    try:
        response = requests.get(f"{API_BASE}/sms")
        data = response.json()
        print(f"Total SMS: {data['count']}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_get_latest_sms():
    print("\nTesting get latest SMS...")
    
    try:
        response = requests.get(f"{API_BASE}/sms/latest?count=5")
        data = response.json()
        print(f"Latest {data['count']} SMS:")
        for sms in data['data']:
            print(f"  - {sms['timestamp']}: {sms['sender']} - {sms['content'][:30]}...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_search_sms():
    print("\nTesting search SMS...")
    
    try:
        response = requests.get(f"{API_BASE}/sms/search/测试")
        data = response.json()
        print(f"Found {data['count']} SMS matching '测试':")
        for sms in data['data']:
            print(f"  - {sms['timestamp']}: {sms['sender']} - {sms['content'][:30]}...")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


def test_health():
    print("\nTesting health check...")
    
    try:
        response = requests.get("http://localhost:8000/health")
        print(f"Health Status: {response.json()}")
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False


if __name__ == "__main__":
    print("=" * 50)
    print("SMS Webhook Server Test Suite")
    print("=" * 50)
    
    tests = [
        ("Health Check", test_health),
        ("Webhook", test_webhook),
        ("Get All SMS", test_get_all_sms),
        ("Get Latest SMS", test_get_latest_sms),
        ("Search SMS", test_search_sms),
    ]
    
    results = []
    for name, test_func in tests:
        print(f"\n{'=' * 50}")
        print(f"Running: {name}")
        print('=' * 50)
        result = test_func()
        results.append((name, result))
    
    print("\n" + "=" * 50)
    print("Test Results Summary")
    print("=" * 50)
    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
