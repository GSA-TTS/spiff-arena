from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAdminPermissions(BaseTest):
    def test_admin_group_permissions_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("perms_group")
        response = client.get(
            f"/v1.0/admin/groups/{group.id}/permissions",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        result = response.json()
        assert "results" in result

    def test_admin_group_permissions_create(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("perms_create_group")
        response = client.post(
            f"/v1.0/admin/groups/{group.id}/permissions",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"permission": "read", "target_uri": "/process-groups/*", "grant_type": "permit"},
        )
        assert response.status_code == 201
        result = response.json()
        assert result["permission"] == "read"
        assert "/process-groups/%" in result["target_uri"]

    def test_admin_group_permissions_delete(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("perms_delete_group")
        # First create a permission
        create_response = client.post(
            f"/v1.0/admin/groups/{group.id}/permissions",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"permission": "read", "target_uri": "/process-models/*"},
        )
        assert create_response.status_code == 201
        permission_id = create_response.json()["id"]

        # Then delete it
        response = client.delete(
            f"/v1.0/admin/groups/{group.id}/permissions/{permission_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200

    def test_admin_group_apply_role_preset(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("preset_group")
        response = client.post(
            f"/v1.0/admin/groups/{group.id}/role-preset",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"process_group_identifier": "test-group", "role": "user"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["permissions_applied"] > 0

    def test_admin_process_group_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = client.get(
            "/v1.0/admin/process-groups-for-permissions",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        result = response.json()
        assert "results" in result
