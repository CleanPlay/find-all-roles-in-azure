# Remediation Guide

Complete guide to fixing Azure RBAC findings from the audit.

## Quick Start

Each GitHub issue contains:
1. **What** — The specific finding (principal, role, scope)
2. **Why It's Risky** — The security risk explanation
3. **How to Fix** — Three remediation options with commands
4. **Least-Privilege Target** — The role you should have instead
5. **Testing & Validation** — Checklist to verify the fix works

---

## Finding Categories & Remediation Patterns

### 🔴 CRITICAL: Service Principal with Owner Role

**Risk:** Service principal can delete entire subscriptions, modify security settings, or exfiltrate data.

**Typical scenarios:**
- Legacy deployment scripts with overly broad permissions
- Testing credentials left in place
- Overly permissive CI/CD pipelines

**Remediation Options:**

**Option 1: Remove if not needed**
```bash
# List the assignment
az role assignment list --assignee <principal-id> --query "[?roleDefinitionName=='Owner']"

# Delete it
az role assignment delete \
  --assignee <principal-id> \
  --role "Owner" \
  --scope "/subscriptions/<subscription-id>"

# Verify deletion
az role assignment list --assignee <principal-id>
```

**Option 2: Replace with least-privilege role**
```bash
# Determine what the principal actually needs
# Common options:
# - "Contributor" (can create/modify resources, but not manage access)
# - Resource-specific roles (e.g., "Web Plan Contributor" for App Service)
# - "Reader" (read-only access)

# Remove Owner
az role assignment delete \
  --assignee <principal-id> \
  --role "Owner" \
  --scope "/subscriptions/<subscription-id>"

# Assign restricted role
az role assignment create \
  --assignee <principal-id> \
  --role "Contributor" \
  --scope "/subscriptions/<subscription-id>"

# Verify
az role assignment list --assignee <principal-id> --query "[].{role:roleDefinitionName,scope:scope}"
```

**Option 3: Scope down to specific resources (if possible)**
```bash
# Remove subscription-level Owner
az role assignment delete \
  --assignee <principal-id> \
  --role "Owner" \
  --scope "/subscriptions/<subscription-id>"

# Assign Contributor to specific resource group instead
az role assignment create \
  --assignee <principal-id> \
  --role "Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<rg-name>"
```

**Testing:**
- [ ] Verify the principal can still perform required operations
- [ ] Test with actual CI/CD pipeline or application
- [ ] Check audit logs for any access denials
- [ ] Re-run the audit script to confirm finding is resolved

**Rollback (if something breaks):**
```bash
# Restore the Owner role temporarily
az role assignment create \
  --assignee <principal-id> \
  --role "Owner" \
  --scope "/subscriptions/<subscription-id>"

# Investigate what failed
# Then try a less restrictive role like Contributor
```

---

### 🟠 HIGH: Service Principal with Contributor Role

**Risk:** Service principal can create, modify, or delete any resource in the scope. Cannot grant access to others.

**Typical scenarios:**
- Deployment service accounts that legitimately need broad access
- Infrastructure-as-Code (IaC) automation accounts
- Development environments (less risky than prod)
- Service accounts for legacy applications

**Assessment:**
- **Subscription-level Contributor:** Usually too broad—reduce scope
- **Resource Group-level Contributor:** More acceptable if scoped to specific applications
- **Resource-level Contributor:** Generally safe (e.g., App Service, Storage Account)

**Remediation Options:**

**Option 1: Verify if actually needed**
```bash
# Check when this role was assigned
az role assignment list \
  --assignee <principal-id> \
  --query "[?roleDefinitionName=='Contributor']" \
  --all

# Check if there are other assignments to this principal
az role assignment list --assignee <principal-id>

# If Contributor is truly needed (e.g., deployment pipeline),
# document the business justification in config/role_whitelist.yaml
```

**Option 2: Scope down from subscription to resource group**
```bash
# Find which resource groups are needed
# (Work with the team that owns the service account)

# Remove subscription-level
az role assignment delete \
  --assignee <principal-id> \
  --role "Contributor" \
  --scope "/subscriptions/<subscription-id>"

# Add to specific resource groups
az role assignment create \
  --assignee <principal-id> \
  --role "Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<rg-name>"
```

**Option 3: Replace with resource-specific role**
```bash
# Identify what type of resource the principal manages
# Example: If it's a deployment account for App Service

# Remove Contributor
az role assignment delete \
  --assignee <principal-id> \
  --role "Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<rg-name>"

# Assign more specific role
az role assignment create \
  --assignee <principal-id> \
  --role "Web Plan Contributor" \
  --scope "/subscriptions/<subscription-id>/resourceGroups/<rg-name>"
```

**Testing:**
- [ ] Run the actual service/deployment that uses this account
- [ ] Verify it can create/update resources it needs
- [ ] Check logs for "Access Denied" errors
- [ ] Test in non-production environment first

**Whitelisting (if Contributor is justified):**

If the service account legitimately needs Contributor access, document it:

```bash
cat >> config/role_whitelist.yaml << 'EOF'
whitelist:
  - principal_id: "<principal-id>"
    role: "Contributor"
    scope: "/subscriptions/<subscription-id>/resourceGroups/<rg-name>"
    reason: "CI/CD deployment pipeline for production infrastructure"
EOF
```

---

## By Principal Type

### Service Principal (Automated Accounts)

Service principals are application identities. They should have **minimal necessary permissions**.

**For CI/CD pipelines:**
- Scope to specific resource groups or resources
- Use "Contributor" (not Owner) if broad access needed
- Use resource-specific roles when possible
- Document the justification

**For application deployments:**
- Assign only the roles needed for that application
- Example: Web app only needs "App Service Contributor"

### Managed Identity (Azure Services)

Managed identities are tied to Azure resources (VMs, Functions, etc.). They should have **exactly the permissions the service needs**.

**For VMs:**
- Scope to specific resource groups
- Use "Reader" if only reading configuration
- Use "Contributor" if managing other resources

**For Functions/App Service:**
- Scope to specific data stores (storage accounts, databases)
- Use service-specific roles (e.g., "Storage Blob Data Contributor")

---

## Remediation Workflow

1. **Pick a finding** from the GitHub issues
2. **Understand the principal**
   ```bash
   az ad sp show --id <principal-id>
   ```
3. **Determine what it actually needs** (talk to the owning team)
4. **Apply the fix** using one of the patterns above
5. **Test thoroughly** in non-prod first
6. **Re-run the audit** to verify the finding is resolved
   ```bash
   python scripts/run_audit.py --dry-run
   ```
7. **Close the GitHub issue** with a comment explaining the fix

---

## Common Mistakes & How to Avoid Them

### ❌ Deleting roles without testing
**Why it fails:** Application or automation breaks immediately in production

**How to avoid:** Always test in non-production environment first

### ❌ Not documenting justified exceptions
**Why it fails:** Next audit cycle flags the same issue again

**How to avoid:** Use `config/role_whitelist.yaml` for documented exceptions

### ❌ Assigning overly specific roles that don't work
**Why it fails:** Role doesn't actually grant needed permissions

**How to avoid:** Test the new role thoroughly before removing the old one

### ❌ Removing access too quickly
**Why it fails:** Unexpected dependencies break in production

**How to avoid:** Keep the old role for 24-48 hours while monitoring, then remove

---

## Role Reference

### Azure Built-In Roles (Common)

| Role | Risk | Use Case |
|------|------|----------|
| **Owner** | 🔴 CRITICAL | Never for service accounts. Rarely for users. |
| **Contributor** | 🟠 HIGH | Deploy infrastructure, manage resources |
| **Reader** | 🟢 LOW | Read-only access to all resources |
| **Virtual Machine Contributor** | 🟡 MEDIUM | Manage VMs (not network/storage) |
| **Web Plan Contributor** | 🟡 MEDIUM | Manage App Service plans |
| **Storage Blob Data Contributor** | 🟡 MEDIUM | Read/write to blob storage |
| **Key Vault Secrets Officer** | 🟠 HIGH | Manage secrets (restrict tightly) |

[Browse all roles](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)

---

## Verification Commands

After applying a fix, verify it worked:

```bash
# Check the specific principal's roles
az role assignment list --assignee <principal-id> \
  --query "[].{role:roleDefinitionName,scope:scope}"

# Verify the old role is gone
az role assignment list --assignee <principal-id> \
  --query "[?roleDefinitionName=='Owner']"
# Should return empty []

# Re-run the audit for this subscription
python scripts/run_audit.py --dry-run

# Check if the finding is gone from the JSON output
grep -c "<principal-id>" output/findings_*.json
```

---

## Need Help?

- **Question about a specific role?** Check the [Azure role docs](https://learn.microsoft.com/en-us/azure/role-based-access-control/built-in-roles)
- **Not sure if a role is safe to remove?** Start a Claude session on the GitHub issue
- **Need to understand the risk better?** Read the "Why It's Risky" section in the issue

See [README.md](../README.md) for running audits and [ARCHITECTURE.md](ARCHITECTURE.md) for how risk is classified.
