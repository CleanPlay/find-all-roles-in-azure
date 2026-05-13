from audit.models import RoleFinding, RiskLevel, PrincipalType
import yaml
from pathlib import Path
from typing import Dict, Optional


class RBACClassifier:
    def __init__(self, config_path: str = "config/risk_rules.yaml"):
        self.config_path = Path(config_path)
        self.rules = self._load_rules()

    def _load_rules(self) -> Dict:
        if not self.config_path.exists():
            return self._default_rules()

        with open(self.config_path) as f:
            return yaml.safe_load(f) or self._default_rules()

    def _default_rules(self) -> Dict:
        return {
            "critical_roles": ["Owner"],
            "high_roles": ["Contributor", "Admin", "Administrator"],
            "medium_roles": [],
            "high_risk_principals": ["ServicePrincipal", "ManagedIdentity"],
            "scope_risk_multiplier": {
                "/": 2.0,
                "/providers/Microsoft.Management/managementGroups/": 1.8,
            },
        }

    def classify(self, finding: RoleFinding) -> RiskLevel:
        role_name = finding.role_name.lower()
        principal_type = finding.principal_type

        if self._is_critical(role_name, principal_type, finding.scope):
            return RiskLevel.CRITICAL

        if self._is_high(role_name, principal_type, finding.scope):
            return RiskLevel.HIGH

        if self._is_medium(role_name, principal_type, finding.scope):
            return RiskLevel.MEDIUM

        return RiskLevel.LOW

    def _is_critical(self, role_name: str, principal_type: PrincipalType, scope: str) -> bool:
        rules = self.rules
        critical_roles = [r.lower() for r in rules.get("critical_roles", [])]

        if any(role_name.startswith(cr) for cr in critical_roles):
            if principal_type == PrincipalType.USER:
                return True
            if principal_type == PrincipalType.SERVICE_PRINCIPAL and scope.count("/") <= 2:
                return True

        return False

    def _is_high(self, role_name: str, principal_type: PrincipalType, scope: str) -> bool:
        rules = self.rules
        high_roles = [r.lower() for r in rules.get("high_roles", [])]

        if any(role_name.startswith(hr) for hr in high_roles):
            if principal_type == PrincipalType.USER:
                return True
            if principal_type == PrincipalType.SERVICE_PRINCIPAL:
                return True
            if principal_type == PrincipalType.MANAGED_IDENTITY and scope.count("/") <= 2:
                return True

        if "custom" in role_name and principal_type in [PrincipalType.SERVICE_PRINCIPAL]:
            return True

        return False

    def _is_medium(self, role_name: str, principal_type: PrincipalType, scope: str) -> bool:
        rules = self.rules
        medium_roles = [r.lower() for r in rules.get("medium_roles", [])]

        if any(role_name.startswith(mr) for mr in medium_roles):
            return True

        if principal_type == PrincipalType.MANAGED_IDENTITY and "owner" in role_name.lower():
            return True

        return False

    def get_risk_reason(self, finding: RoleFinding, risk_level: RiskLevel) -> str:
        principal_type_str = finding.principal_type.value
        scope_level = "subscription" if "/subscriptions/" in finding.scope and finding.scope.count("/") == 3 else "resource group" if "/resourceGroups/" in finding.scope else "tenant"

        reasons = {
            RiskLevel.CRITICAL: f"{principal_type_str} '{finding.principal_name}' has {finding.role_name} role at {scope_level} scope. This allows unrestricted access to modify or delete any resource.",
            RiskLevel.HIGH: f"{principal_type_str} '{finding.principal_name}' has {finding.role_name} role at {scope_level} scope. This allows broad permissions to modify resources.",
            RiskLevel.MEDIUM: f"{principal_type_str} '{finding.principal_name}' has {finding.role_name} role at {scope_level} scope. Consider if this level of access is necessary.",
            RiskLevel.LOW: f"{principal_type_str} '{finding.principal_name}' has {finding.role_name} role. Read-only access is generally safe.",
        }

        return reasons.get(risk_level, "")

    def get_recommended_role(self, finding: RoleFinding) -> Optional[str]:
        role_lower = finding.role_name.lower()

        if "owner" in role_lower or "contributor" in role_lower:
            if "storage" in finding.scope.lower():
                return "Storage Blob Data Contributor"
            if "key" in finding.scope.lower() or "keyvault" in finding.scope.lower():
                return "Key Vault Secrets Officer"
            return "Contributor"

        return None
