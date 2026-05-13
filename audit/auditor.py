import logging
from typing import List, Set
from audit.models import RoleFinding, RiskLevel, PrincipalType
from audit.azure_client import AzureClient
from audit.rbac_classifier import RBACClassifier


class RBACauditor:
    def __init__(self):
        self.azure_client = AzureClient()
        self.classifier = RBACClassifier()
        self.logger = self._setup_logger()
        self.findings: List[RoleFinding] = []

    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("rbac-auditor")
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    def run_audit(self) -> List[RoleFinding]:
        self.logger.info("Starting Azure RBAC audit")
        self.findings = []

        subscriptions = self.azure_client.get_subscriptions()
        self.logger.info(f"Found {len(subscriptions)} subscription(s)")

        for sub in subscriptions:
            self.logger.info(f"Scanning subscription: {sub['name']} ({sub['id']})")
            self._audit_subscription(sub)

        self.logger.info(f"Audit complete. Found {len(self.findings)} findings")
        return self.findings

    def _audit_subscription(self, subscription: dict):
        sub_id = subscription["id"]
        sub_name = subscription["name"]

        try:
            assignments = self.azure_client.get_role_assignments(sub_id)
            self.logger.info(f"Found {len(assignments)} role assignments")

            for assignment in assignments:
                finding = self._process_assignment(assignment, sub_id, sub_name)
                if finding:
                    self.findings.append(finding)

        except Exception as e:
            self.logger.error(f"Error auditing subscription {sub_name}: {e}")

    def _process_assignment(self, assignment: dict, sub_id: str, sub_name: str) -> RoleFinding | None:
        principal_id = assignment["principal_id"]
        principal_name = assignment.get("principal_name", "Unknown")
        role_id = assignment["role_definition_id"]
        scope = assignment["scope"]

        try:
            role_def = self.azure_client.get_role_definition(sub_id, role_id)
            role_name = role_def.get("role_name", "Unknown")

            principal_type_str = self._infer_principal_type(principal_id, principal_name)
            principal_type = self._parse_principal_type(principal_type_str)

            scope_type = self._get_scope_type(scope)

            finding = RoleFinding(
                subscription_name=sub_name,
                subscription_id=sub_id,
                principal_name=principal_name,
                principal_id=principal_id,
                principal_type=principal_type,
                role_name=role_name,
                role_id=role_id,
                scope=scope,
                scope_type=scope_type,
                risk_level=RiskLevel.LOW,
                risk_reason="",
            )

            risk_level = self.classifier.classify(finding)
            finding.risk_level = risk_level
            finding.risk_reason = self.classifier.get_risk_reason(finding, risk_level)
            finding.recommended_role = self.classifier.get_recommended_role(finding)

            if risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]:
                return finding

            return None

        except Exception as e:
            self.logger.warning(f"Error processing assignment {principal_id}: {e}")
            return None

    def _infer_principal_type(self, principal_id: str, principal_name: str) -> str:
        if principal_name and "@" in principal_name:
            return "User"
        if principal_name and principal_name.startswith("mi-"):
            return "ManagedIdentity"
        return "ServicePrincipal"

    def _parse_principal_type(self, principal_type_str: str) -> PrincipalType:
        type_map = {
            "User": PrincipalType.USER,
            "ServicePrincipal": PrincipalType.SERVICE_PRINCIPAL,
            "ManagedIdentity": PrincipalType.MANAGED_IDENTITY,
            "Group": PrincipalType.GROUP,
        }
        return type_map.get(principal_type_str, PrincipalType.UNKNOWN)

    def _get_scope_type(self, scope: str) -> str:
        if "/subscriptions/" in scope and "/resourceGroups/" not in scope:
            return "Subscription"
        if "/resourceGroups/" in scope:
            return "ResourceGroup"
        if "/providers/" in scope:
            return "Resource"
        return "Tenant"

    def filter_findings_by_risk(self, risk_level: RiskLevel) -> List[RoleFinding]:
        return [f for f in self.findings if f.risk_level == risk_level]

    def get_findings_summary(self) -> dict:
        return {
            "total": len(self.findings),
            "critical": len(self.filter_findings_by_risk(RiskLevel.CRITICAL)),
            "high": len(self.filter_findings_by_risk(RiskLevel.HIGH)),
            "medium": len(self.filter_findings_by_risk(RiskLevel.MEDIUM)),
            "low": len(self.filter_findings_by_risk(RiskLevel.LOW)),
        }
