# Azure RBAC Audit & Least-Privilege Remediation

Automated identification and remediation of overly permissive Azure role assignments across your entire tenant.

## Overview

This project continuously audits Azure RBAC to find users and service accounts with risky permissions—Owner, Contributor, or custom admin roles—and generates actionable remediation tasks prioritized by risk.

**Key features:**
- Scans all subscriptions for excessive role assignments
- Classifies findings by risk (human users > service accounts > custom roles > broad scopes)
- Auto-generates GitHub issues with step-by-step remediation instructions
- Tracks changes across audit runs (detects new, resolved, or modified findings)
- Safe, read-only access using Azure service principal with minimal permissions

## Quick Start

### Prerequisites
- Owner/admin access to Azure tenant
- Python 3.9+ (for running the audit locally)
- GitHub repo with write access (for creating issues)

### Setup

1. **Create Azure service principal** (read-only auditor identity)
   - See [Phase 1 Setup Guide](#phase-1-service-principal-setup)

2. **Configure local environment**
   ```bash
   cp .env.example .env.local
   # Edit .env.local with your Azure tenant/app IDs and GitHub token
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Validate Azure access**
   ```bash
   python scripts/test_azure_access.py
   ```

5. **Run first audit (dry-run)**
   ```bash
   python scripts/run_audit.py --dry-run
   ```

6. **Create GitHub issues**
   ```bash
   python scripts/run_audit.py --create-issues
   ```

## Project Structure

```
.
├── audit/                 # Core audit logic
│   ├── azure_client.py   # Azure SDK wrapper
│   ├── auditor.py        # Main orchestration
│   ├── rbac_classifier.py # Risk classification
│   └── models.py         # Data models
├── github_integration/    # GitHub issue creation
├── scripts/              # Entry points
│   ├── run_audit.py      # Main audit script
│   └── test_azure_access.py
├── config/               # Risk rules, whitelists
├── docs/                 # Detailed documentation
├── tests/                # Unit tests
└── output/               # (gitignored) Audit findings & logs
```

## Audit Flow

1. **Enumerate** all subscriptions in tenant
2. **Query** role assignments (users, service principals, managed identities)
3. **Classify** each assignment by risk level
4. **Filter** findings (skip safe/expected assignments)
5. **Generate** GitHub issues with remediation steps
6. **Track** changes (new/resolved/modified findings)

### Risk Levels

| Priority | Finding | Example |
|----------|---------|---------|
| 🔴 **CRITICAL** | Human with Owner role | User account could delete entire subscription |
| 🟠 **HIGH** | Service principal with Contributor | Compromised account can modify resources |
| 🟡 **MEDIUM** | Managed identity with Owner on single resource | Lower blast radius, may be necessary |
| 🟢 **LOW** | Reader role (any principal) | Read-only, minimal risk |

## Documentation

- **[SETUP.md](docs/SETUP.md)** — Step-by-step Phase 1 (service principal creation)
- **[ARCHITECTURE.md](docs/ARCHITECTURE.md)** — Technical design & implementation details
- **[REMEDIATION.md](docs/REMEDIATION.md)** — How to fix findings from audit
- **[CLAUDE.md](CLAUDE.md)** — Project goals & audit principles

## Status

- [x] Project structure & plan
- [x] Phase 1: Service principal setup
- [ ] Phase 2: Python audit implementation
- [ ] Phase 3: GitHub integration
- [ ] Phase 4: Testing & dry-run
- [ ] Phase 5: First full audit run
- [ ] Phase 6: Scheduled audits (GitHub Actions)

## Running Audits

### Manual (local)
```bash
source .env.local
python scripts/run_audit.py --create-issues
```

### Scheduled (GitHub Actions)
See [.github/workflows/audit_schedule.yml](.github/workflows/audit_schedule.yml) for weekly automated audits.

## Configuration

Edit `config/risk_rules.yaml` to customize:
- Which roles are considered high-risk
- Scope-based adjustments (e.g., subscription vs. resource-level)
- Role whitelists (intentional high-privilege assignments)

## Safety & Security

- ✅ **Read-only:** Service principal uses Azure "Reader" role—cannot modify resources
- ✅ **Minimal permissions:** No access to secrets, credentials, or data
- ✅ **Credential isolation:** Secrets stored only in `.env.local` (never committed)
- ✅ **Audit logging:** All audit runs logged with timestamp, findings, and changes
- ⚠️ **Secret rotation:** Client secret expires in 2 years—set calendar reminder

## Contributing

Issues & findings are tracked as [GitHub issues](../../issues) and prioritized by risk level.

---

**Questions?** See [FAQ.md](docs/FAQ.md) or review [CLAUDE.md](CLAUDE.md) for project context.
