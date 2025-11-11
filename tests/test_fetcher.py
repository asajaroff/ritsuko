#!/usr/bin/env python3
"""Simple test script for nautobot fetcher"""
import os
import sys

# Set up environment
os.environ['NAUTOBOT_TOKEN'] = "REDACTED"
os.environ['NAUTOBOT_URL'] = "https://REDACTED.REDACTED/api"

# Add src to path
sys.path.insert(0, 'src')

from fetchers import get_nautobot_devices

# Test with different queries
test_queries = ['c001', 'aus', 'aus1p1', 'node']

for query in test_queries:
    print(f"\n{'='*60}")
    print(f"Testing get_nautobot_devices with '{query}'...")
    print('='*60)
    try:
        result = get_nautobot_devices(query)
        if result:
            print(f"Success! Found {len(result)} device(s):")
            for dev in result:
                print(dev)
        else:
            print("No devices found.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
