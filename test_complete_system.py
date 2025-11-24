"""
Complete system test script.
Tests all components and the full doorbell workflow.
"""

import asyncio
import requests
import json
from pathlib import Path


def print_section(title: str):
    """Print a section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def test_api_health():
    """Test if API is running."""
    print_section("🏥 Testing API Health")

    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            print(f"✅ API is healthy!")
            print(f"   Environment: {data['environment']}")
            print(f"   Version: {data['version']}")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API is not running: {e}")
        print("\n💡 Start the API with:")
        print("   python src/main.py")
        return False


def test_password_matching():
    """Test password matching endpoint."""
    print_section("🔐 Testing Password Matching")

    test_cases = [
        ("alohomora", True, "Exact match"),
        ("alo mora", True, "Fuzzy match with space"),
        ("mellon", True, "Second password"),
        ("wrong password", False, "Wrong password"),
    ]

    all_passed = True

    for text, should_match, description in test_cases:
        try:
            response = requests.post(
                f"http://localhost:8000/test/password?text={text}",
                timeout=5
            )

            if response.status_code == 200:
                data = response.json()
                matched = data["match"]
                score = data["score"]

                if matched == should_match:
                    symbol = "✅"
                else:
                    symbol = "❌"
                    all_passed = False

                print(f"{symbol} '{text}' - {description}")
                print(f"   Match: {matched}, Score: {score:.2f}%")
            else:
                print(f"❌ Request failed with status: {response.status_code}")
                all_passed = False

        except Exception as e:
            print(f"❌ Error testing '{text}': {e}")
            all_passed = False

    return all_passed


def test_audio_files():
    """Check if audio files exist."""
    print_section("🎵 Checking Audio Files")

    required_files = [
        "witch_password.mp3",
        "witch_welcome.mp3",
        "witch_wrong.mp3",
        "witch_denied.mp3",
        "witch_repeat.mp3",
    ]

    audio_dir = Path("audio_assets")
    all_exist = True

    for filename in required_files:
        filepath = audio_dir / filename
        if filepath.exists():
            size = filepath.stat().st_size / 1024
            if size > 0:
                print(f"✅ {filename} ({size:.1f} KB)")
            else:
                print(f"⚠️  {filename} (0 KB - empty file)")
                all_exist = False
        else:
            print(f"❌ {filename} (missing)")
            all_exist = False

    return all_exist


def test_complete_workflow():
    """Test the complete doorbell workflow."""
    print_section("🚪 Testing Complete Doorbell Workflow")

    print("Starting complete workflow test...")
    print("This simulates a full doorbell event:\n")

    try:
        response = requests.post(
            "http://localhost:8000/test/complete-flow",
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()

            print(f"📊 Workflow Result:")
            print(f"   Status: {data['status'].upper()}")
            print(f"   Attempts: {data.get('attempts', 0)}")

            if data['status'] == 'success':
                print(f"   ✅ Matched Password: {data.get('matched_password')}")
                print(f"   Confidence: {data.get('score', 0):.2f}%")
                print("\n✅ Complete workflow PASSED!")
                return True
            elif data['status'] == 'denied':
                print(f"   🚫 Access denied: {data.get('reason')}")
                print("\n⚠️  Workflow completed but access was denied")
                return True  # Still counts as successful test
            else:
                print(f"\n❌ Unexpected status: {data['status']}")
                return False

        else:
            print(f"❌ Request failed with status: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Error testing workflow: {e}")
        return False


def test_webhook_endpoint():
    """Test the webhook endpoint."""
    print_section("🔗 Testing Webhook Endpoint")

    try:
        response = requests.post(
            "http://localhost:8000/webhooks/ring/doorbell",
            timeout=30
        )

        if response.status_code == 200:
            data = response.json()
            print(f"✅ Webhook endpoint working!")
            print(f"   Status: {data['status']}")
            print(f"   Device: {data.get('session', {}).get('device_id', 'N/A')}")
            return True
        else:
            print(f"❌ Webhook failed with status: {response.status_code}")
            return False

    except Exception as e:
        print(f"❌ Error testing webhook: {e}")
        return False


def run_all_tests():
    """Run all system tests."""
    print("\n" + "="*60)
    print("  🧙‍♀️ Ring Ring Who's There - System Test")
    print("="*60)

    results = {}

    # Test 1: API Health
    results["API Health"] = test_api_health()

    if not results["API Health"]:
        print("\n❌ Cannot continue tests - API is not running!")
        return

    # Test 2: Password Matching
    results["Password Matching"] = test_password_matching()

    # Test 3: Audio Files
    results["Audio Files"] = test_audio_files()

    # Test 4: Complete Workflow
    results["Complete Workflow"] = test_complete_workflow()

    # Test 5: Webhook Endpoint
    results["Webhook Endpoint"] = test_webhook_endpoint()

    # Summary
    print_section("📊 Test Summary")

    total = len(results)
    passed = sum(1 for v in results.values() if v)

    for test_name, passed_test in results.items():
        symbol = "✅" if passed_test else "❌"
        print(f"{symbol} {test_name}")

    print(f"\n{'='*60}")
    print(f"  Total: {passed}/{total} tests passed")

    if passed == total:
        print(f"  🎉 All tests PASSED!")
    else:
        print(f"  ⚠️  Some tests failed")

    print(f"{'='*60}\n")


if __name__ == "__main__":
    run_all_tests()
