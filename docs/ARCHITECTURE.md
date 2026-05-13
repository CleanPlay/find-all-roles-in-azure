# Architecture & Technical Design

Complete technical reference for the Azure RBAC audit system.

---

## System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                     Azure RBAC Auditor                       │
└─────────────────────────────────────────────────────────────┘

    ┌──────────────────────────────────────────────────────┐
    │  scripts/run_audit.py (CLI Entry Point)              │
    │  - --dry-run: Show findings without creating issues  │
    │  - --create-issues: Create GitHub issues             │
    └──────────────────────────────────────────────────────┘
                         │
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐   ┌─────▼──────┐   ┌────▼──────────┐
    │  Auditor  │   │  Classifier │   │  GitHub      │
    │           │   │             │   │  Integration │
    │ - Query   │   │ - Risk      │   │              │
    │   Azure   │   │   levels    │   │ - Create     │
    │ - Process │   │ - Rules     │   │   issues     │
    │   findings│   │ - Patterns  │   │ - Templates  │
    └─────┬─────┘   └─────┬──────┘   └────┬──────────┘
          │               │               │
          │               │               │
    ┌─────▼───────────────▼───────────────▼──────┐
    │         Azure SDK (Management API)          │
    │  - subscriptions.list()                     │
    │  - roleAssignments.list_for_subscription()  │
    │  - roleDefinitions.get_by_id()              │
    └─────────────────────────────────────────────┘
          │
          ▼
    ┌─────────────────┐
    │  Azure Tenant   │
    │  (All data)     │
    └─────────────────┘
```

---

## Authentication Strategy

### Service Principal (Not Personal Account)

**Why not use personal credentials?**
- Personal accounts are tied to individuals
- Access cannot be revoked independently
- Difficult to audit who ran what
- Credentials cannot be rotated without impacting the person

**Service Principal Benefits:**
- Isolated identity for the audit tool
- Can be rotated/revoked independently
- Fully auditable (who made the call is clear)
- Can be revoked without impacting humans
- Can be scoped to specific permissions

### Client Secret Auth Flow

```
1. Service Principal created in Azure AD
2. Client secret generated (2-year expiry)
3. Credentials stored in .env.local (never committed)
4. Azure CLI uses ClientSecretCredential
5. Credential rotated annually before expiry
```

**Credential Storage:**
- `.env.local` — Local machine only (in .gitignore)
- GitHub Actions — Uses GitHub Secrets (not checked in)
- Never committed to git or shared

---

## Azure SDK Query Patterns

### Step 1: Enumerate Subscriptions

```python
from azure.mgmt.subscription import SubscriptionClient

client = SubscriptionClient(credential)
subscriptions = client.subscriptions.list()

for sub in subscriptions:
    print(sub.subscription_id, sub.display_name)
```

**What it returns:**
- Subscription ID: `12345678-1234-1234-1234-123456789012`
- Display name: `MySubscription`
- State: `Enabled` or `Disabled`

### Step 2: Query Role Assignments

```python
from azure.mgmt.authorization import AuthorizationManagementClient

client = AuthorizationManagementClient(credential, subscription_id)
assignments = client.role_assignments.list_for_subscription()

for assignment in assignments:
    print(assignment.principal_id)        # UUID of user/app
    print(assignment.role_definition_id)  # UUID of the role
    print(assignment.scope)               # /subscriptions/...
```

**What it returns:**
- `principal_id`: The user, service principal, or managed identity
- `role_definition_id`: Which role is assigned
- `scope`: Where the role applies
- `principal_type`: User, ServicePrincipal, ManagedIdentity, Group

### Step 3: Get Role Definition

```python
role_def = client.role_definitions.get_by_id(role_definition_id)

print(role_def.role_name)    # "Owner", "Contributor", "Reader"
print(role_def.permissions)  # List of allowed actions
```

**What it returns:**
- `role_name`: Human-readable role name
- `permissions`: List of actions allowed
  - `"*"` = all actions (Owner/Contributor)
  - Specific patterns like `"Microsoft.Storage/*/read"`

### Complexity: Scope Hierarchy

Azure has a scope hierarchy:

```
Tenant Root (/)
  ├─ Management Group
  │   └─ Subscription
  │       └─ Resource Group
  │           └─ Resource
```

**Our audit scans:**
- Subscriptions (level 2)
- Resource groups (level 3)
- Resources (level 4)

**We do NOT scan:**
- Tenant root (would need tenant admin)
- Management groups (optional, not in current scope)

---

## Risk Classification Algorithm

### Classification Logic

The `RBACClassifier` class implements the risk decision tree:

```python
def classify(finding: RoleFinding) -> RiskLevel:
    
    # CRITICAL: Owner role on any user, or Owner on SP at subscription level
    if role == "Owner":
        if principal_type == User:
            return CRITICAL
        if principal_type == ServicePrincipal and scope_level <= 2:
            return CRITICAL
    
    # HIGH: Contributor on any service principal or managed identity at sub level
    if role == "Contributor":
        if principal_type in [ServicePrincipal, ManagedIdentity]:
            if scope_level <= 2:
                return HIGH
    
    # MEDIUM: Owner/Contributor on managed identity at resource level
    if principal_type == ManagedIdentity:
        if role in ["Owner", "Contributor"]:
            return MEDIUM
    
    # LOW: Reader role (safe, read-only)
    return LOW
```

### Risk Factors

| Factor | Weight | Example |
|--------|--------|---------|
| Role | 🔴 High | Owner > Contributor > Reader |
| Principal Type | 🟠 Medium | User > ServicePrincipal > ManagedIdentity |
| Scope | 🟡 Low | Subscription > ResourceGroup > Resource |
| Custom Role | 🟠 Medium | Custom roles analyzed for dangerous permissions |

### Why These Rules?

**Owner at subscription level = CRITICAL:**
- Can delete entire subscription
- Can modify security settings
- Can change Role-Based Access Control (RBAC) itself
- Acceptable only for users with accountability

**Contributor = HIGH:**
- Can create, modify, delete resources
- Cannot grant access (less dangerous than Owner)
- Needs justification if at subscription level
- More acceptable at resource group level

**Reader = LOW:**
- Read-only, no modifications possible
- Lowest risk

**Managed Identity at resource level = MEDIUM:**
- Azure-managed, cannot be compromised externally
- Scoped to single resource is safer
- But still needs the principle of least privilege

---

## GitHub Integration Design

### Issue Template Format

Each issue follows this structure:

```markdown
## Security Finding: [Principal] has [Role] on [Scope]

**Risk Level:** [CRITICAL/HIGH/MEDIUM]

### What
- **Principal:** [Name or ID]
- **Current Role:** [Role name]
- **Subscription:** [Subscription name]
- **Scope:** [Subscription/ResourceGroup/Resource]

### Why It's Risky
[Risk explanation specific to finding]

### How to Fix
[3 remediation options with Azure CLI commands]

### Least-Privilege Target
- **Recommended Role:** [Role]
- **Reasoning:** [Why this is safer]

### Testing & Validation
[Checklist for verifying the fix]
```

### Idempotency

The issue creator is **idempotent**:

```python
def create_or_update_findings(findings):
    for finding in findings:
        # Search for existing issue
        existing = search_github(finding)
        
        if existing:
            update_issue(existing, finding)  # Update if changed
        else:
            create_issue(finding)  # Create new if not found
```

**Benefits:**
- Re-running the audit won't create duplicate issues
- Issue updates if the finding changes (e.g., role was partially removed)
- Safe to run multiple times

### GitHub Search Query

```python
search_query = f'repo:{repo} is:open "{principal_id[:8]}" "{role_name}"'
```

Searches for open issues containing:
- First 8 characters of principal ID
- Role name (e.g., "Owner", "Contributor")

---

## Data Flow: Complete Audit Run

```
1. Load credentials from .env.local
   └─ AZURE_TENANT_ID, AZURE_CLIENT_ID, AZURE_CLIENT_SECRET
   
2. Authenticate to Azure
   └─ ClientSecretCredential exchanges secret for access token
   
3. Get list of subscriptions
   └─ SubscriptionClient.subscriptions.list()
   
4. For each subscription:
   
   a. Get role assignments
      └─ AuthorizationManagementClient.role_assignments.list_for_subscription()
      
   b. For each assignment:
      
      i.   Get role definition
           └─ AuthorizationManagementClient.role_definitions.get_by_id()
           
      ii.  Classify risk
           └─ RBACClassifier.classify(finding)
           
      iii. Store finding if HIGH or CRITICAL
           └─ findings.append(finding)
   
5. Save findings to JSON
   └─ output/findings_YYYY-MM-DD.json
   
6. For each finding:
   
   a. Search GitHub for existing issue
      └─ gh.search_issues(query)
      
   b. Create or update issue
      └─ repo.create_issue() or issue.edit()
      
7. Log summary
   └─ Total, CRITICAL, HIGH, MEDIUM, LOW counts
```

---

## Configuration

### Risk Rules (config/risk_rules.yaml)

```yaml
critical_roles:
  - Owner

high_roles:
  - Contributor
  - Admin

# Service principals are riskier than managed identities
high_risk_principals:
  - ServicePrincipal
  - ManagedIdentity
```

**Customization:** Edit this file to adjust what's considered high-risk for your environment.

### Role Whitelist

```yaml
whitelist:
  - principal_id: "12345678-1234-1234-1234-123456789012"
    role: "Contributor"
    scope: "/subscriptions/xxx/resourceGroups/yyy"
    reason: "CI/CD deployment service, required for IaC"
```

Issues for whitelisted assignments are not created.

---

## Performance & Scale

### Query Volume

For 2 subscriptions with ~40 role assignments each:
- 1 request to list subscriptions
- 1 request per subscription to list role assignments
- 1 request per role assignment to get role definition
- **Total:** ~85 API requests

**Time:** ~1-2 minutes (includes network latency)

### Optimization Opportunities

1. **Cache role definitions** — Avoid re-fetching same role IDs
2. **Batch requests** — Use batch API for multiple role definitions
3. **Parallel subscriptions** — Query subscriptions concurrently

Currently not optimized for scale, but acceptable for small-to-medium deployments.

---

## Error Handling

### Scenarios Handled

| Scenario | Handling |
|----------|----------|
| Invalid credentials | Fail at auth time (clear error) |
| Missing permissions | Return empty list (user just doesn't have access) |
| Invalid subscription ID | Skip that subscription, log warning |
| Network timeout | Retry once, then skip and continue |
| GitHub rate limit | Wait or fail gracefully |

### Fail-Safe Design

If a single subscription fails, the audit continues with others. This prevents a single bad subscription from blocking the entire audit.

---

## Security & Threat Model

### What This Audit Can and Cannot Do

**Can do (Read-only):**
- ✅ List all subscriptions
- ✅ Enumerate role assignments
- ✅ Read role definitions
- ✅ Query principal IDs

**Cannot do (Write protection):**
- ❌ Modify role assignments
- ❌ Delete roles
- ❌ Change security settings
- ❌ Access secrets or data

**Why Reader role is sufficient:**
The service principal has `Reader` role, which includes `*/read` permissions but excludes `*/write`.

### If Service Principal is Compromised

- Attacker can enumerate Azure RBAC configuration
- Attacker cannot modify any Azure resources
- The compromised principal can be revoked immediately
- Access is isolated to read-only audit activity

**Mitigation:**
- Rotate client secret annually
- Monitor Azure activity logs for this principal
- Revoke immediately if suspicious activity detected
- Use different credentials for different environments

---

## Extending the Audit

### Adding Custom Rules

Edit `audit/rbac_classifier.py`:

```python
def _is_critical(self, role_name, principal_type, scope):
    # Add your custom rule here
    if "custom_dangerous_role" in role_name.lower():
        return True
```

### Adding Custom Scope Analysis

```python
def _get_scope_risk(self, scope):
    # Score scope by how much access it grants
    if "tenant" in scope:
        return 2.0  # Highest risk
    if "resourceGroups" not in scope:
        return 1.0  # Subscription level
    return 0.5     # Resource level (lowest)
```

### Integrating with Other Tools

- **Export to SIEM:** Modify `run_audit.py` to send findings to your SIEM
- **Slack notifications:** Add webhook to notify on new CRITICAL findings
- **Custom dashboard:** Parse findings JSON and build visualization

---

## Debugging

### Enable Verbose Logging

```bash
# Azure SDK debug logs
AZURE_SDK_LOG_LEVEL=DEBUG python scripts/run_audit.py --dry-run

# All logs
python -u scripts/run_audit.py --dry-run 2>&1 | tee audit.log
```

### Inspect Findings JSON

```bash
# Pretty print findings
python -m json.tool output/findings_*.json

# Query specific findings
jq '.findings[] | select(.risk_level=="CRITICAL")' output/findings_*.json

# Count by type
jq '[.findings[] | .principal_type] | group_by(.) | map({type: .[0], count: length})' output/findings_*.json
```

### Test Azure Access

```bash
python scripts/test_azure_access.py
```

This validates all Azure SDK connectivity before running the full audit.

---

See [REMEDIATION.md](REMEDIATION.md) for how to fix findings and [README.md](../README.md) for operational documentation.
