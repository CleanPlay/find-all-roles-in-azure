# Phase 1: Service Principal Setup

This guide walks you through creating an Azure service principal with read-only access to audit your entire tenant's RBAC configuration.

## What You'll Create

A **service principal** is an application identity in Azure AD that can authenticate programmatically. We'll create one specifically for the RBAC audit with:
- **Scope:** Tenant-wide (all subscriptions)
- **Permissions:** Reader role only (read-only, no modifications allowed)
- **Auth method:** Client secret (stored securely in `.env.local`)
- **Lifetime:** 2 years (client secret expires; you'll rotate it)

## Prerequisites

- **Azure tenant admin or Owner role** — You need to create an app registration
- **Azure CLI** (optional, makes this faster)
  ```bash
  # Install: https://learn.microsoft.com/en-us/cli/azure/install-azure-cli
  # Verify:
  az --version
  ```
- **Text editor** to save credentials safely

## Step 1: Create the App Registration

### Option A: Using Azure CLI (Recommended)

**1.1 Authenticate to Azure**
```bash
az login
```

Follow the browser prompt to sign in with your tenant admin account.

**1.2 Create the app registration**
```bash
az ad app create --display-name "CleanPlay-RBAC-Auditor"
```

**Save the output.** You need:
```
"appId": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"  ← SAVE THIS (AZURE_CLIENT_ID)
"id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"     ← App object ID
```

**1.3 Create a service principal from the app**
```bash
az ad sp create --id <appId>
```

**Save the output.** You need:
```
"id": "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"     ← SAVE THIS (Service Principal Object ID)
```

### Option B: Using Azure Portal

If you prefer the UI:

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **App registrations**
3. Click **New registration**
4. **Name:** `CleanPlay-RBAC-Auditor`
5. **Supported account types:** "Accounts in this organizational directory only"
6. Click **Register**
7. Copy **Application (client) ID** — save as `AZURE_CLIENT_ID`
8. Copy **Directory (tenant) ID** — save as `AZURE_TENANT_ID`

Then create a service principal:
- In the app's **Overview** page, note the **Object ID**

---

## Step 2: Assign the Reader Role (Tenant-Wide)

The service principal needs **Reader** role at the tenant root scope to enumerate all subscriptions and role assignments.

### Option A: Using Azure CLI (Recommended)

```bash
# Get your tenant ID
TENANT_ID=$(az account show --query tenantId -o tsv)

# Get the service principal object ID
SP_OBJECT_ID=$(az ad sp show --id <appId> --query id -o tsv)

# Assign Reader role at tenant root
az role assignment create \
  --assignee <SP_OBJECT_ID> \
  --role "Reader" \
  --scope "/"
```

**Verify:**
```bash
az role assignment list --assignee <SP_OBJECT_ID>
```

You should see:
```
{
  "principalName": "CleanPlay-RBAC-Auditor",
  "roleDefinitionName": "Reader",
  "scope": "/"
}
```

### Option B: Using Azure Portal

1. Go to [portal.azure.com](https://portal.azure.com)
2. Search for **Subscriptions**
3. Select your subscription (or navigate to **Tenant root**)
4. Click **Access control (IAM)** on the left
5. Click **Add** → **Add role assignment**
6. **Role:** Reader
7. **Assign access to:** User, group, or service principal
8. **Select:** Search for "CleanPlay-RBAC-Auditor", select it
9. Click **Review + assign**

---

## Step 3: Create a Client Secret

The client secret is the "password" for the service principal. Store it securely in `.env.local`.

### Using Azure CLI

```bash
az ad app credential create --id <appId> --years 2
```

**Output:**
```json
{
  "customKeyIdentifier": null,
  "displayName": null,
  "endDate": "2028-05-12T...",
  "hint": "...",
  "keyId": "...",
  "password": "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",  ← SAVE THIS (AZURE_CLIENT_SECRET)
  "startDate": "2026-05-12T..."
}
```

**⚠️ IMPORTANT:** Copy the `password` field immediately—you won't be able to see it again. If you lose it, you'll need to create a new one.

### Using Azure Portal

1. Go to your app registration in [portal.azure.com](https://portal.azure.com)
2. Click **Certificates & secrets** on the left
3. Click **New client secret**
4. **Description:** `RBAC Audit`
5. **Expires:** `24 months`
6. Click **Add**
7. Copy the **Value** immediately—you won't see it again

---

## Step 4: Gather Your Credentials

Collect these values (you'll use them in the next step):

```
AZURE_TENANT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_ID=xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
AZURE_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_REPO=your-username/your-repo-name
```

**Where to get each:**

| Variable | Source |
|----------|--------|
| `AZURE_TENANT_ID` | Azure Portal → [Directory settings](https://portal.azure.com/#settings/directory) → Copy "Tenant ID" |
| `AZURE_CLIENT_ID` | Azure Portal → App registration → **Application (client) ID** |
| `AZURE_CLIENT_SECRET` | Created in Step 3 above |
| `AZURE_SUBSCRIPTION_ID` | Azure Portal → Subscriptions → Copy "Subscription ID" (any subscription in your tenant) |
| `GITHUB_TOKEN` | GitHub → [Settings → Developer settings → Personal access tokens](https://github.com/settings/tokens) → Create new token with `repo` scope |
| `GITHUB_REPO` | Your GitHub repo (format: `owner/repo-name`) |

---

## Step 5: Configure .env.local

**Never commit `.env.local` to git.**

1. **Copy the template:**
   ```bash
   cd /Users/dgrandquist/Projects/CleanPlay/find-all-roles-in-azure
   cp .env.example .env.local
   ```

2. **Edit `.env.local` with your credentials:**
   ```bash
   # .env.local
   AZURE_TENANT_ID=your-tenant-id
   AZURE_CLIENT_ID=your-client-id
   AZURE_CLIENT_SECRET=your-client-secret
   AZURE_SUBSCRIPTION_ID=any-subscription-id
   
   GITHUB_TOKEN=your-github-personal-access-token
   GITHUB_REPO=your-username/find-all-roles-in-azure
   ```

3. **Verify `.env.local` is in `.gitignore`:**
   ```bash
   grep "\.env\.local" .gitignore
   ```

---

## Step 6: Validate the Setup

### 6.1 Create `.env.example` (template without secrets)

```bash
cat > .env.example << 'EOF'
# Azure credentials for RBAC Auditor service principal
AZURE_TENANT_ID=your-tenant-id-here
AZURE_CLIENT_ID=your-client-id-here
AZURE_CLIENT_SECRET=your-client-secret-here
AZURE_SUBSCRIPTION_ID=any-subscription-id-in-your-tenant

# GitHub credentials for issue creation
GITHUB_TOKEN=your-github-personal-access-token
GITHUB_REPO=owner/repo-name
EOF
```

### 6.2 Test Azure authentication

We'll create a simple test script to verify the service principal works:

```bash
cat > scripts/test_azure_access.py << 'EOF'
#!/usr/bin/env python3
"""
Test Azure service principal authentication.
Safe to run — read-only only.
"""

import os
import sys
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
EOF
chmod +x scripts/test_azure_access.py
```

**Run the test:**
```bash
# Install dependencies first
pip install python-dotenv azure-identity azure-mgmt-subscription azure-mgmt-authorization

# Run test
python scripts/test_azure_access.py
```

**Expected output:**
```
Testing Azure credentials...
✓ Successfully authenticated
✓ Found 3 subscription(s):
  - Production (xxx-xxx-xxx)
  - Staging (xxx-xxx-xxx)
  - Dev (xxx-xxx-xxx)
✓ Found 42 role assignments in first subscription

✅ All tests passed! Service principal is configured correctly.
```

### 6.3 Troubleshooting

| Error | Solution |
|-------|----------|
| `Invalid client secret` | Copy the secret again from Azure Portal (you can't retrieve old secrets) |
| `Credentials object has expired` | Create a new client secret; delete the old one |
| `Access denied` | Verify service principal has Reader role at `/` scope: `az role assignment list --assignee <sp-id>` |
| `Subscription not found` | Verify `AZURE_SUBSCRIPTION_ID` is valid in this tenant |

---

## Next Steps

Once **Step 6** passes:

1. ✅ **Phase 1 Complete:** Service principal is set up and validated
2. **Phase 2:** Install Python dependencies and build audit script
3. **Phase 3:** Test audit in dry-run mode
4. **Phase 4:** Create GitHub integration
5. **Phase 5:** Run first full audit

See [README.md](../README.md) for the next phase.

---

## Security Best Practices

### Client Secret Management
- ✅ **DO:** Store in `.env.local` only (gitignored)
- ✅ **DO:** Rotate every 2 years (set calendar reminder for 2028-05)
- ✅ **DO:** Delete old secrets after rotating
- ❌ **DON'T:** Commit to git or share in Slack/email
- ❌ **DON'T:** Hardcode in scripts
- ❌ **DON'T:** Log or print in debug output

### Least-Privilege
- ✅ **Reader role only** — Cannot modify, delete, or access data
- ✅ **Tenant root scope** — Sees all subscriptions
- ❌ **Not Owner or Contributor** — Too permissive
- ❌ **Not with resource access** — Audit doesn't need data plane access

### Monitoring
- Regularly review role assignments: `az role assignment list --all`
- Delete the service principal if audit project is abandoned
- Monitor for unexpected credential rotations (indicates potential breach)

---

## FAQ

**Q: Can I use my personal credentials instead of a service principal?**
A: Not recommended. The service principal is isolated, auditable, and can be deleted without affecting your account.

**Q: What if I lose the client secret?**
A: Create a new one in Azure Portal. The old one is automatically invalid.

**Q: Does the service principal need write permissions?**
A: No. Reader role is sufficient and safer. Write operations will be rejected by Azure.

**Q: Can I limit the service principal to specific subscriptions?**
A: Yes. Assign Reader role to specific resource groups instead of `/` scope. Update `config/risk_rules.yaml` accordingly.

**Q: How do I rotate the client secret?**
A: Create a new secret in Azure Portal, update `.env.local`, delete the old secret, done.
