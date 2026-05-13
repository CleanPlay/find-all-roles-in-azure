#!/usr/bin/env python3
"""
Test Azure service principal authentication.
Safe to run — read-only only.
"""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv

# Load .env.local
load_dotenv('.env.local')

def test_connection():
    try:
        from azure.identity import ClientSecretCredential
        from azure.mgmt.subscription import SubscriptionClient

        print("Testing Azure credentials...")

        credential = ClientSecretCredential(
            tenant_id=os.getenv("AZURE_TENANT_ID"),
            client_id=os.getenv("AZURE_CLIENT_ID"),
            client_secret=os.getenv("AZURE_CLIENT_SECRET")
        )

        client = SubscriptionClient(credential)
        subs = list(client.subscriptions.list())

        print(f"✓ Successfully authenticated")
        print(f"✓ Found {len(subs)} subscription(s):")
        for sub in subs:
            print(f"  - {sub.display_name} ({sub.subscription_id})")

        # Test authorization client on first subscription
        if subs:
            from azure.mgmt.authorization import AuthorizationManagementClient

            sub = subs[0]
            auth_client = AuthorizationManagementClient(credential, sub.subscription_id)
            assignments = list(auth_client.role_assignments.list_for_subscription())
            print(f"✓ Found {len(assignments)} role assignments in first subscription")
            print("\n✅ All tests passed! Service principal is configured correctly.")

        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Verify .env.local has correct credentials")
        print("2. Check service principal has Reader role (az role assignment list --assignee <sp-id>)")
        print("3. Ensure credentials haven't expired")
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)
