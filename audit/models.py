from dataclasses import dataclass, asdict
from typing import Optional
from enum import Enum


class RiskLevel(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PrincipalType(str, Enum):
    USER = "User"
    SERVICE_PRINCIPAL = "ServicePrincipal"
    MANAGED_IDENTITY = "ManagedIdentity"
    GROUP = "Group"
    UNKNOWN = "Unknown"


@dataclass
class RoleFinding:
    subscription_name: str
    subscription_id: str
    principal_name: str
    principal_id: str
    principal_type: PrincipalType
    role_name: str
    role_id: str
    scope: str
    scope_type: str
    risk_level: RiskLevel
    risk_reason: str
    recommended_role: Optional[str] = None
    recommended_scope: Optional[str] = None

    def to_dict(self):
        data = asdict(self)
        data['principal_type'] = self.principal_type.value
        data['risk_level'] = self.risk_level.value
        return data

    def __eq__(self, other):
        if not isinstance(other, RoleFinding):
            return False
        return (
            self.subscription_id == other.subscription_id
            and self.principal_id == other.principal_id
            and self.role_id == other.role_id
            and self.scope == other.scope
        )

    def __hash__(self):
        return hash((self.subscription_id, self.principal_id, self.role_id, self.scope))
