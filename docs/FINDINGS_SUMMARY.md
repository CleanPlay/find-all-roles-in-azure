# Audit Findings Summary

Complete list of all 20 findings from the initial Azure RBAC audit (May 13, 2026).

**Status:** All findings converted to GitHub issues #6-#23

---

## Overview

| Risk Level | Count | GitHub Issues |
|-----------|-------|---------------|
| 🔴 **CRITICAL** | 5 | [#2](#critical-owner-role-on-subscription), [#12](#critical-owner-role-on-subscription-1), [#19](#critical-owner-role-on-subscription-2), [#20](#critical-owner-role-on-subscription-3), [#23](#critical-owner-role-on-subscription-4) |
| 🟠 **HIGH** | 15 | [#6](#high-contributor-on-subscription), [#7](#high-contributor-on-resource-group), [#8](#high-contributor-on-resource-group-1), [#9](#high-contributor-on-subscription-1), etc. |

---

## 🔴 CRITICAL: Owner Role on Subscription

### Issue: Service Principal with Owner on Microsoft Azure Sponsorship

**GitHub Issue:** #2  
**Principal ID:** `57ec7933-d313-4fcd-bbb6-74692f7e1a34`  
**Principal Type:** ServicePrincipal  
**Scope:** `/subscriptions/7f149ad1-a70b-49e9-bc70-5c194e78afab` (Microsoft Azure Sponsorship)  

**Risk:** Owner role at subscription scope. Can delete entire subscription, modify security settings, or exfiltrate all data.

**Remediation:** Remove Owner role and assign Contributor if needed. [Details →](../README.md#-critical-service-principal-with-owner-role)

---

### Issue: Service Principal with Owner on Microsoft Azure Sponsorship (2)

**GitHub Issue:** #19  
**Principal ID:** `57ec7933-d313-4fcd-bbb6-74692f7e1a34` (same as above)  
**Principal Type:** ServicePrincipal  
**Scope:** `/subscriptions/7f149ad1-a70b-49e9-bc70-5c194e78afab`  

**Status:** Duplicate of #2. Likely system role that appears multiple times.

---

### Issue: Service Principal with Owner on Microsoft Azure Sponsorship (3)

**GitHub Issue:** #20  
**Principal ID:** `57ec7933-d313-4fcd-bbb6-74692f7e1a34` (same)  
**Scope:** `/subscriptions/7f149ad1-a70b-49e9-bc70-5c194e78afab`  

**Status:** Duplicate of #2 and #19.

---

### Issue: Service Principal with Owner on CleanPlay Dev Subscription

**GitHub Issue:** #12  
**Principal ID:** `f9af0213-ac3b-43f2-9a02-2e4940d4558d`  
**Principal Type:** ServicePrincipal  
**Scope:** `/subscriptions/2a34a41c-a0f6-4c9f-8e5d-6a4cfd3d61e5` (CleanPlay Dev Subscription)  

**Risk:** Owner role at subscription scope on dev environment. Still dangerous but lower blast radius than production.

**Remediation:** Replace with Contributor or resource-specific role.

---

### Issue: Service Principal with Owner on CleanPlay Dev Subscription (2)

**GitHub Issue:** #23  
**Principal ID:** `f9af0213-ac3b-43f2-9a02-2e4940d4558d` (same as #12)  
**Scope:** `/subscriptions/2a34a41c-a0f6-4c9f-8e5d-6a4cfd3d61e5`  

**Status:** Duplicate of #12.

---

## 🟠 HIGH: Contributor Role (Subscription-Level)

These service principals can create/modify/delete resources but cannot change access control.

### Issues on Microsoft Azure Sponsorship Subscription

| Issue | Principal ID | Principal | Scope |
|-------|--------------|-----------|-------|
| #1 | `0f89f8c2...` | ServicePrincipal | Subscription |
| #4 | `17338078...` | ServicePrincipal | Subscription |
| #5 | `5ee32bcc...` | ServicePrincipal | Subscription |
| #9 | `c07ec9cb...` | ServicePrincipal | Subscription |
| #10 | `46d994ec...` | ServicePrincipal | Subscription |
| #14 | `46d994ec...` | ServicePrincipal | Subscription (duplicate) |
| #13 | `97bf6002...` | ServicePrincipal | Subscription |
| #18 | `92ddbbac...` | ServicePrincipal | Subscription |

**Remediation:** Determine if each principal legitimately needs Contributor. If yes, consider scoping to specific resource groups. If no, remove.

### Issues on CleanPlay Dev Subscription

| Issue | Principal ID | Principal | Scope |
|-------|--------------|-----------|-------|
| #3 | `0f89f8c2...` | ServicePrincipal | Subscription |
| #6 | `ea6ca1e0...` | ServicePrincipal | ResourceGroup |
| #7 | `9e00e8c1...` | ServicePrincipal | ResourceGroup |
| #8 | `2910490b...` | ServicePrincipal | ResourceGroup |
| #11 | `0f89f8c2...` | ServicePrincipal | ResourceGroup |
| #15 | `ea6ca1e0...` | ServicePrincipal | Resource |
| #16 | `f9af0213...` | ServicePrincipal | ResourceGroup |
| #17 | `ea6ca1e0...` | ServicePrincipal | ResourceGroup |

---

## Remediation Priority

### Immediate (Do First)
1. **CRITICAL Owner roles** — Issues #2, #12, #19, #20, #23
   - High risk of accidental or malicious damage
   - Replace with Contributor or resource-specific roles

### High Priority (Do Next)
2. **Subscription-level Contributor** on production subscription
   - Issues #1, #4, #5, #9, #10, #13, #14, #18
   - Scope down to specific resource groups
   - Verify each has legitimate need

### Medium Priority (Do After)
3. **Resource Group/Resource-level Contributor** on dev subscription
   - Issues #3, #6, #7, #8, #11, #15, #16, #17
   - May be legitimate for development
   - Verify ownership and need

---

## Remediation Workflow

For each GitHub issue (in priority order):

1. **Read the issue** — Understand the principal, role, and scope
2. **Investigate** — Who owns this account? Why does it need this role?
3. **Decide** — Keep, reduce scope, or remove?
4. **Fix** — Apply the remediation steps from REMEDIATION.md
5. **Test** — Verify in non-prod environment
6. **Verify** — Re-run audit or check manually
7. **Close** — Comment on the issue with what you did

---

## For Claude Sessions

When starting a Claude session to work on a GitHub issue:

1. **Copy the issue link** into the Claude session
2. **Provide context:**
   ```
   I'm remediating GitHub issue #X from an Azure RBAC audit.
   The issue is: [paste the issue description]
   
   Can you help me:
   1. Understand what this principal needs
   2. Determine the best remediation approach
   3. Provide step-by-step commands to fix it
   4. Help me test the fix
   ```
3. **Follow the remediation steps** from the issue
4. **Test the fix** using the verification commands
5. **Post results** back to the GitHub issue

---

## Next Steps

1. ✅ Initial audit complete (20 findings identified)
2. ✅ GitHub issues created (#6-#23)
3. ⬜ Start remediation (GitHub issues)
4. ⬜ Re-run audit after fixes
5. ⬜ Set up scheduled weekly audits

See [REMEDIATION.md](REMEDIATION.md) for detailed fix instructions for each finding type.
