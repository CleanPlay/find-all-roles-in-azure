# Frequently Asked Questions

## Setup & Authentication

**Q: Do I need owner access to create the service principal?**
A: You need to be able to create app registrations in Azure AD (usually admin or application developer role). Owner role is sufficient but not necessary.

**Q: Can I use my personal credentials instead?**
A: Not recommended. Service principals are better for audits—they're isolated, auditable, and can be revoked without affecting your account.

**Q: What if I lose the client secret?**
A: Create a new one in Azure Portal. The old one becomes invalid immediately.

## Running Audits

**Q: Is it safe to run the audit on production?**
A: Yes. The service principal has read-only permissions. It cannot modify, delete, or access resource data.

**Q: How often should I run the audit?**
A: Weekly is recommended (see GitHub Actions setup). At minimum monthly to catch drift.

**Q: Can I run the audit on specific subscriptions only?**
A: Yes. Assign the service principal Reader role to specific subscriptions instead of tenant root (`/`).

## Findings & Remediation

**Q: What if a high-risk finding is actually needed?**
A: Document the exception in `config/role_whitelist.yaml` with justification, then re-run the audit to suppress it.

**Q: How do I know if removing a role will break something?**
A: Test in a non-prod subscription first. Use Azure role assignment preview to simulate changes.

**Q: Can the audit track historical changes?**
A: Yes, by comparing `output/findings_*.json` across audit runs.

## Security

**Q: Is it safe to store the client secret in `.env.local`?**
A: Yes, if `.env.local` is in `.gitignore` (it is) and you don't share it. For CI/CD, use Azure KeyVault or GitHub Secrets.

**Q: How do I rotate the client secret?**
A: Create a new secret in Azure Portal, update `.env.local`, delete the old secret.

**Q: What permissions does the service principal need?**
A: Reader role only. This allows reading role assignments and enumerating users/service accounts without modification access.

---

See [SETUP.md](SETUP.md) for Phase 1 details, [REMEDIATION.md](REMEDIATION.md) for fixing findings.
