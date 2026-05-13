import os
from typing import List, Dict, Optional
from azure.identity import ClientSecretCredential
from azure.mgmt.subscription import SubscriptionClient
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import ClientAuthenticationError


class AzureClient:
    def __init__(self):
        self.tenant_id = os.getenv("AZURE_TENANT_ID")
        self.client_id = os.getenv("AZURE_CLIENT_ID")
        self.client_secret = os.getenv("AZURE_CLIENT_SECRET")
        self.subscription_id = os.getenv("AZURE_SUBSCRIPTION_ID")

        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Missing required Azure credentials in environment")

        self.credential = ClientSecretCredential(
            tenant_id=self.tenant_id,
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    def get_subscriptions(self) -> List[Dict]:
        try:
            client = SubscriptionClient(self.credential)
            subscriptions = []
            for sub in client.subscriptions.list():
                subscriptions.append({
                    "id": sub.subscription_id,
                    "name": sub.display_name,
                    "state": sub.state,
                })
            return subscriptions
        except ClientAuthenticationError as e:
            raise Exception(f"Failed to authenticate: {e}")

    def get_role_assignments(self, subscription_id: str) -> List[Dict]:
        try:
            client = AuthorizationManagementClient(self.credential, subscription_id)
            assignments = []

            for assignment in client.role_assignments.list_for_subscription():
                assignments.append({
                    "id": assignment.id,
                    "principal_id": assignment.principal_id,
                    "principal_name": getattr(assignment, "principal_name", None),
                    "role_definition_id": assignment.role_definition_id,
                    "scope": assignment.scope,
                })

            return assignments
        except Exception as e:
            raise Exception(f"Failed to get role assignments for {subscription_id}: {e}")

    def get_role_definition(self, subscription_id: str, role_id: str) -> Dict:
        try:
            client = AuthorizationManagementClient(self.credential, subscription_id)
            role_def = client.role_definitions.get_by_id(role_id)
            return {
                "id": role_def.id,
                "name": role_def.name,
                "role_name": role_def.role_name,
                "type": role_def.type,
                "permissions": role_def.permissions,
            }
        except Exception as e:
            raise Exception(f"Failed to get role definition {role_id}: {e}")

    def get_principal_type(self, subscription_id: str, principal_id: str) -> str:
        try:
            client = AuthorizationManagementClient(self.credential, subscription_id)
            role_assignments = client.role_assignments.list_for_subscription()

            for assignment in role_assignments:
                if assignment.principal_id == principal_id:
                    return assignment.principal_type

            return "Unknown"
        except Exception as e:
            return "Unknown"
