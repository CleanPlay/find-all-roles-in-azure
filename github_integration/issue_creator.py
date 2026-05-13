import os
import logging
from typing import List, Tuple
from github import Github
from github.GithubException import GithubException
from audit.models import RoleFinding, RiskLevel


class GitHubIssueCreator:
    def __init__(self):
        self.token = os.getenv("GITHUB_TOKEN")
        self.repo_name = os.getenv("GITHUB_REPO")
        self.logger = logging.getLogger("github-creator")

        if not self.token or not self.repo_name:
            raise ValueError("Missing GITHUB_TOKEN or GITHUB_REPO environment variables")

        self.gh = Github(self.token)
        self.repo = self.gh.get_repo(self.repo_name)

    def create_or_update_findings(self, findings: List[RoleFinding]) -> Tuple[int, int, int]:
        created = 0
        updated = 0
        closed = 0

        for finding in findings:
            issue_number = self._find_existing_issue(finding)

            if issue_number:
                self._update_issue(issue_number, finding)
                updated += 1
            else:
                self._create_issue(finding)
                created += 1

        self.logger.info(f"GitHub: Created {created}, Updated {updated}, Closed {closed}")
        return created, updated, closed

    def _find_existing_issue(self, finding: RoleFinding) -> int | None:
        search_query = f'repo:{self.repo.full_name} is:open "{finding.principal_name}" "{finding.role_name}"'

        try:
            issues = self.gh.search_issues(search_query)
            for issue in issues:
                if self._is_matching_finding(issue, finding):
                    return issue.number
        except GithubException as e:
            self.logger.warning(f"Error searching for existing issue: {e}")

        return None

    def _is_matching_finding(self, issue, finding: RoleFinding) -> bool:
        return (
            finding.principal_name in issue.title
            and finding.role_name in issue.title
            and finding.subscription_name in issue.body
        )

    def _create_issue(self, finding: RoleFinding):
        title = f"[{finding.risk_level}] {finding.principal_name} has {finding.role_name} on {finding.scope_type}"
        body = self._generate_issue_body(finding)
        labels = [finding.risk_level.lower(), "azure-rbac", "security"]

        try:
            issue = self.repo.create_issue(
                title=title,
                body=body,
                labels=labels,
            )
            self.logger.info(f"Created issue #{issue.number}: {title}")
        except GithubException as e:
            self.logger.error(f"Failed to create issue: {e}")

    def _update_issue(self, issue_number: int, finding: RoleFinding):
        try:
            issue = self.repo.get_issue(issue_number)
            body = self._generate_issue_body(finding)
            issue.edit(body=body)
            self.logger.info(f"Updated issue #{issue_number}")
        except GithubException as e:
            self.logger.error(f"Failed to update issue #{issue_number}: {e}")

    def _generate_issue_body(self, finding: RoleFinding) -> str:
        scope_level = "subscription" if "/subscriptions/" in finding.scope and finding.scope.count("/") == 3 else "resource group" if "/resourceGroups/" in finding.scope else "tenant"

        fix_options = f"""
**Option 1: Remove Overly Permissive Role** (if not needed)
```bash
az role assignment delete \\
  --assignee "{finding.principal_id}" \\
  --role "{finding.role_name}" \\
  --scope "{finding.scope}"
```

**Option 2: Reduce Scope** (if access is needed)
```bash
# Remove current assignment
az role assignment delete \\
  --assignee "{finding.principal_id}" \\
  --role "{finding.role_name}" \\
  --scope "{finding.scope}"

# Assign to more specific scope
az role assignment create \\
  --assignee "{finding.principal_id}" \\
  --role "Reader" \\
  --scope "<more-specific-scope>"
```

**Option 3: Replace with Least-Privilege Role**
```bash
az role assignment create \\
  --assignee "{finding.principal_id}" \\
  --role "{finding.recommended_role or 'Reader'}" \\
  --scope "{finding.scope}"
```
"""

        return f"""## Security Finding: {finding.principal_name} has {finding.role_name} on {finding.scope_type}

**Risk Level:** 🔴 {finding.risk_level.value}

### What
- **Principal:** {finding.principal_name} ({finding.principal_type.value})
- **Current Role:** {finding.role_name}
- **Subscription:** {finding.subscription_name}
- **Scope:** {finding.scope_type}
- **Full Scope:** `{finding.scope}`

### Why It's Risky
{finding.risk_reason}

### How to Fix
{fix_options}

### Least-Privilege Target
- **Recommended Role:** {finding.recommended_role or 'Reader'}
- **Reasoning:** Provides necessary access without unnecessary permissions

### Testing & Validation
- [ ] Verify principal can still perform required actions
- [ ] Test in non-production environment first
- [ ] Confirm no automated systems break after change
- [ ] Run `az role assignment list --assignee "{finding.principal_id}"` to verify

---
_Generated by Azure RBAC Auditor | Last updated: {self._get_timestamp()}_
"""

    def _get_timestamp(self) -> str:
        from datetime import datetime
        return datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
