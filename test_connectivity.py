#!/usr/bin/env python3
"""
Zabbix to Slack Connector - Connectivity Test Script
This script validates the configuration before running the full connector
"""

import sys
import json

print("=" * 70)
print("ZABBIX TO SLACK CONNECTOR - CONNECTIVITY TEST")
print("=" * 70)
print()

# Test 1: Check Python version
print("Test 1: Checking Python version...")
if sys.version_info >= (3, 6):
    print(f"✅ PASS - Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
else:
    print(f"❌ FAIL - Python {sys.version_info.major}.{sys.version_info.minor} (requires 3.6+)")
    sys.exit(1)
print()

# Test 2: Check required modules
print("Test 2: Checking required Python modules...")
required_modules = ['requests', 'json', 'datetime']
missing_modules = []

for module in required_modules:
    try:
        __import__(module)
        print(f"✅ {module}")
    except ImportError:
        print(f"❌ {module} - NOT FOUND")
        missing_modules.append(module)

if missing_modules:
    print(f"\n❌ FAIL - Missing modules: {', '.join(missing_modules)}")
    print("Install with: pip3 install requests --break-system-packages")
    sys.exit(1)
else:
    print("✅ PASS - All required modules found")
print()

# Test 3: Test Zabbix API connection
print("Test 3: Testing Zabbix API connection...")
try:
    sys.path.append('api')
    from methods import ZABBIX_API_URL, AUTHTOKEN
    
    if "YOUR_API" in ZABBIX_API_URL or not AUTHTOKEN:
        print("❌ FAIL - Zabbix credentials not configured")
        print("Please edit api/methods.py with your Zabbix credentials")
        sys.exit(1)
    
    print(f"✅ Zabbix URL: {ZABBIX_API_URL}")
    print(f"✅ Authentication token received: {AUTHTOKEN[:20]}...")
    print("✅ PASS - Zabbix API connection successful")
except Exception as e:
    print(f"❌ FAIL - Zabbix API connection error: {str(e)}")
    print("\nPossible issues:")
    print("- Check Zabbix URL is correct")
    print("- Verify username/password")
    print("- Ensure network connectivity to Zabbix server")
    print("- Check if Zabbix API is enabled")
    sys.exit(1)
print()

# Test 4: Test Zabbix problem retrieval
print("Test 4: Testing Zabbix problem retrieval...")
try:
    from methods import get_all_problems
    problems = get_all_problems()
    
    if problems is not None:
        print(f"✅ PASS - Retrieved {len(problems)} problems from Zabbix")
        if len(problems) > 0:
            print(f"   Sample problem: {problems[0].get('name', 'N/A')}")
    else:
        print("⚠️  WARNING - No problems retrieved (this may be normal if no active problems)")
except Exception as e:
    print(f"❌ FAIL - Error retrieving problems: {str(e)}")
    sys.exit(1)
print()

# Test 5: Test Slack webhook configuration
print("Test 5: Testing Slack webhook configuration...")
try:
    from slack_notifier import SLACK_WEBHOOK_URL
    
    if "YOUR_SLACK_WEBHOOK" in SLACK_WEBHOOK_URL or not SLACK_WEBHOOK_URL.startswith("https://hooks.slack.com"):
        print("❌ FAIL - Slack webhook not configured")
        print("Please edit api/slack_notifier.py with your Slack webhook URL")
        print("\nTo create a webhook:")
        print("1. Go to https://api.slack.com/apps")
        print("2. Create a new app or select existing")
        print("3. Enable 'Incoming Webhooks'")
        print("4. Create webhook for your channel")
        sys.exit(1)
    
    print(f"✅ Webhook URL configured: {SLACK_WEBHOOK_URL[:50]}...")
    print("✅ PASS - Slack webhook configured")
except Exception as e:
    print(f"❌ FAIL - Error checking Slack configuration: {str(e)}")
    sys.exit(1)
print()

# Test 6: Send test Slack notification
print("Test 6: Sending test notification to Slack...")
try:
    from slack_notifier import send_simple_slack_message
    from datetime import datetime
    
    test_message = f"🧪 Test message from Zabbix to Slack Connector - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    result = send_simple_slack_message(test_message)
    
    if result:
        print("✅ PASS - Test notification sent successfully!")
        print("   Check your Slack channel for the test message")
    else:
        print("❌ FAIL - Failed to send test notification")
        print("   Check Slack webhook URL and network connectivity")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL - Error sending test notification: {str(e)}")
    print("\nPossible issues:")
    print("- Verify webhook URL is correct")
    print("- Check network connectivity to Slack")
    print("- Ensure webhook is active in Slack app settings")
    sys.exit(1)
print()

# Test 7: Send formatted test alert
print("Test 7: Sending formatted test alert to Slack...")
try:
    from slack_notifier import send_slack_notification
    from datetime import datetime
    
    result = send_slack_notification(
        event_id="TEST-12345",
        hostname="test-server",
        visible_name="Test Server",
        problem_name="This is a test alert from the connector validation",
        severity="Medium",
        timestamp=datetime.now(),
        group_name="Test Group"
    )
    
    if result:
        print("✅ PASS - Formatted test alert sent successfully!")
        print("   Check your Slack channel for the formatted alert")
    else:
        print("❌ FAIL - Failed to send formatted alert")
        sys.exit(1)
except Exception as e:
    print(f"❌ FAIL - Error sending formatted alert: {str(e)}")
    sys.exit(1)
print()

# Test 8: Check file structure
print("Test 8: Checking file structure...")
import os

required_files = [
    'zabbix_to_slack.sh',
    'api/methods.py',
    'api/get_problems.py',
    'api/get_all_problems_nok.py',
    'api/slack_notifier.py'
]

missing_files = []
for file in required_files:
    if os.path.exists(file):
        print(f"✅ {file}")
    else:
        print(f"❌ {file} - NOT FOUND")
        missing_files.append(file)

if missing_files:
    print(f"\n❌ FAIL - Missing files: {', '.join(missing_files)}")
    sys.exit(1)
else:
    print("✅ PASS - All required files present")
print()

# Test 9: Check script permissions
print("Test 9: Checking script permissions...")
if os.access('zabbix_to_slack.sh', os.X_OK):
    print("✅ PASS - zabbix_to_slack.sh is executable")
else:
    print("⚠️  WARNING - zabbix_to_slack.sh is not executable")
    print("   Run: chmod +x zabbix_to_slack.sh")
print()

# Final summary
print("=" * 70)
print("CONNECTIVITY TEST COMPLETED SUCCESSFULLY! ✅")
print("=" * 70)
print()
print("Next steps:")
print("1. Review the test messages in your Slack channel")
print("2. If everything looks good, start the connector:")
print("   nohup ./zabbix_to_slack.sh > nohup.out 2>&1 &")
print()
print("3. Monitor the logs:")
print("   tail -f log.txt")
print()
print("4. To stop the connector:")
print("   ps -ef | grep zabbix_to_slack.sh")
print("   kill -9 <PID>")
print()
