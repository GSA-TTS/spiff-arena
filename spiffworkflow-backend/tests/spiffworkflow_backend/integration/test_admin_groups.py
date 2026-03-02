from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAdminGroups(BaseTest):
    def test_admin_group_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        UserService.find_or_create_group("test_group_1")
        UserService.find_or_create_group("test_group_2")

        response = client.get(
            "/v1.0/admin/groups",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        result = response.json()
        assert result["pagination"]["total"] >= 2
        identifiers = [g["identifier"] for g in result["results"]]
        assert "test_group_1" in identifiers
        assert "test_group_2" in identifiers

    def test_admin_group_create(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        response = client.post(
            "/v1.0/admin/groups",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"identifier": "new_test_group", "name": "New Test Group"},
        )
        assert response.status_code == 201
        result = response.json()
        assert result["identifier"] == "new_test_group"
        assert result["name"] == "New Test Group"

    def test_admin_group_create_duplicate(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        UserService.find_or_create_group("dup_group")
        response = client.post(
            "/v1.0/admin/groups",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"identifier": "dup_group"},
        )
        assert response.status_code == 400

    def test_admin_group_show(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("show_group")
        UserService.add_user_to_group(with_super_admin_user, group)

        response = client.get(
            f"/v1.0/admin/groups/{group.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        result = response.json()
        assert result["identifier"] == "show_group"
        assert len(result["members"]) >= 1
        assert isinstance(result["pending"], list)

    def test_admin_group_update(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("update_group")
        response = client.put(
            f"/v1.0/admin/groups/{group.id}",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"name": "Updated Name"},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["name"] == "Updated Name"

    def test_admin_group_delete(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("delete_group")
        group_id = group.id
        response = client.delete(
            f"/v1.0/admin/groups/{group_id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert db.session.get(GroupModel, group_id) is None

    def test_admin_group_add_members(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("member_group")
        user = self.find_or_create_user("member_test_user")

        response = client.post(
            f"/v1.0/admin/groups/{group.id}/members",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"usernames": [user.username]},
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["added"]) == 1

    def test_admin_group_add_members_creates_pending_for_unknown_user(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("pending_group")

        response = client.post(
            f"/v1.0/admin/groups/{group.id}/members",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"usernames": ["nonexistent@example.com"]},
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["pending"]) == 1
        assert result["pending"][0]["username"] == "nonexistent@example.com"

    def test_admin_group_remove_member(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("remove_member_group")
        user = self.find_or_create_user("removable_user")
        UserService.add_user_to_group(user, group)

        response = client.delete(
            f"/v1.0/admin/groups/{group.id}/members/{user.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200

    def test_admin_group_remove_pending(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("remove_pending_group")
        wugam = UserGroupAssignmentWaitingModel(username="pending_user@example.com", group_id=group.id)
        db.session.add(wugam)
        db.session.commit()

        response = client.delete(
            f"/v1.0/admin/groups/{group.id}/pending/{wugam.id}",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        assert db.session.get(UserGroupAssignmentWaitingModel, wugam.id) is None

    def test_admin_pending_list(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("pending_list_group")
        wugam = UserGroupAssignmentWaitingModel(username="future_user@example.com", group_id=group.id)
        db.session.add(wugam)
        db.session.commit()

        response = client.get(
            "/v1.0/admin/pending-assignments",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        result = response.json()
        assert result["pagination"]["total"] >= 1

    def test_admin_reprocess_pending(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("reprocess_group")
        # Create user first, then create a waiting assignment manually afterward.
        # This simulates the scenario where the waiting assignment was created before
        # the user existed, but the user has since logged in (creating their account),
        # and apply_waiting_group_assignments missed this assignment.
        user = self.find_or_create_user("reprocess_user")
        # Manually insert a waiting assignment (bypassing apply_waiting_group_assignments)
        wugam = UserGroupAssignmentWaitingModel(username=user.username, group_id=group.id)
        db.session.add(wugam)
        db.session.commit()
        # Expire the session to force a refresh on the pending list
        db.session.expire_all()

        response = client.post(
            f"/v1.0/admin/groups/{group.id}/pending/reprocess",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200, f"Expected 200 but got {response.status_code}: {response.text}"
        result = response.json()
        assert len(result["resolved"]) == 1

    def test_admin_group_member_annotation_update(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        group = UserService.find_or_create_group("annotation_group")
        user = self.find_or_create_user("annotated_user")
        UserService.add_user_to_group(user, group)

        response = client.put(
            f"/v1.0/admin/groups/{group.id}/members/{user.id}/annotation",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"annotation": "Team lead"},
        )
        assert response.status_code == 200
