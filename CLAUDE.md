# Azure RBAC Audit & Least-Privilege Remediation

## Goal
Identify all users and service accounts with overly permissive roles (Owner, Contributor, custom admin roles) across our entire Azure tenant. Generate actionable remediation tasks prioritized by risk.

## Scope
- All subscriptions in the Azure tenant
- Both human users and service accounts (managed identities, service principals)
- Current role assignments at any scope (subscription, resource group, resource level)

## Risk Ordering (highest to lowest)
1. Human users with Owner/Contributor/Admin roles
2. Service accounts (managed identities, service principals) with Owner/Contributor/Admin roles
3. Custom admin-equivalent roles
4. Overly broad scope assignments (e.g., tenant-level when should be resource-level)

## Output Format
For each finding, create a task with:

- **What:** [User/Service Account name] has [Role] on [Scope]
- **Why it's risky:** [Specific risk — credential compromise, accidental changes, compliance violation]
- **How to fix:** Step-by-step instructions (CLI/Portal/IaC) to:
  - Remove overly permissive role
  - Assign least-privilege replacement role(s)
  - Test/validate the change doesn't break workflows
- **Least-privilege target:** Specific role(s) they should have instead + reasoning
- **Acceptance criteria:** How we verify the fix worked

## Design Principles
- **Continuous use:** This is an ongoing audit. Re-run regularly to catch drift and new issues. Flag changes since the last scan if possible.
- **Safety first:** Err toward caution—flag edge cases, note if a role removal might break something, suggest testing in non-prod first.

## Current Status
- [ ] Set up safe access for scanning Azure infrastructure
- [ ] Determine output format for tasks (Linear, Asana, etc.)
- [ ] Establish baseline of current Azure RBAC assignments
- [ ] Begin ongoing audit and remediation cycle
