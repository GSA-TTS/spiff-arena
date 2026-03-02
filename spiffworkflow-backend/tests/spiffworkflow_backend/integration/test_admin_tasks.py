import time

from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.user_service import UserService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestAdminTasks(BaseTest):
    def _create_test_process_instance_with_human_task(
        self, user: UserModel
    ) -> tuple[ProcessInstanceModel, HumanTaskModel]:
        """Create a minimal process instance and human task for testing."""
        pi = ProcessInstanceModel(
            process_model_identifier="test/model",
            process_model_display_name="Test Model",
            process_initiator_id=user.id,
            status="waiting",
            updated_at_in_seconds=int(time.time()),
            created_at_in_seconds=int(time.time()),
        )
        db.session.add(pi)
        db.session.commit()

        ht = HumanTaskModel(
            process_instance_id=pi.id,
            task_id="test-task-guid",
            task_name="test_task",
            task_title="Test Task",
            task_type="UserTask",
            task_status="READY",
            process_model_display_name="Test Model",
            bpmn_process_identifier="TestProcess",
            completed=False,
            updated_at_in_seconds=int(time.time()),
            created_at_in_seconds=int(time.time()),
        )
        db.session.add(ht)
        db.session.commit()

        htu = HumanTaskUserModel(
            human_task_id=ht.id,
            user_id=user.id,
            added_by=HumanTaskUserAddedBy.process_initiator.value,
        )
        db.session.add(htu)
        db.session.commit()

        return pi, ht

    def test_admin_pi_tasks(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        pi, _ht = self._create_test_process_instance_with_human_task(with_super_admin_user)

        response = client.get(
            f"/v1.0/admin/process-instances/{pi.id}/tasks",
            headers=self.logged_in_headers(with_super_admin_user),
        )
        assert response.status_code == 200
        result = response.json()
        assert "results" in result
        assert "process_instance" in result
        assert len(result["results"]) == 1

    def test_admin_task_add_owners(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        _pi, ht = self._create_test_process_instance_with_human_task(with_super_admin_user)
        new_user = self.find_or_create_user("added_owner_user")

        response = client.put(
            f"/v1.0/admin/tasks/{ht.id}/add-owners",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"user_ids": [new_user.id]},
        )
        assert response.status_code == 200
        result = response.json()
        owner_ids = [o["id"] for o in result["potential_owners"]]
        assert new_user.id in owner_ids

    def test_admin_task_reassign(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        _pi, ht = self._create_test_process_instance_with_human_task(with_super_admin_user)
        new_user = self.find_or_create_user("reassigned_user")

        response = client.put(
            f"/v1.0/admin/tasks/{ht.id}/reassign",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"user_ids": [new_user.id]},
        )
        assert response.status_code == 200
        result = response.json()
        owner_ids = [o["id"] for o in result["potential_owners"]]
        assert new_user.id in owner_ids
        # Should have replaced existing owners
        assert with_super_admin_user.id not in owner_ids

    def test_admin_task_lane_reassign(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        _pi, ht = self._create_test_process_instance_with_human_task(with_super_admin_user)
        ht.lane_name = "test_lane"
        db.session.add(ht)
        db.session.commit()

        group = UserService.find_or_create_group("lane_group")
        lane_user = self.find_or_create_user("lane_user")
        UserService.add_user_to_group(lane_user, group)

        response = client.put(
            f"/v1.0/admin/tasks/{ht.id}/lane-reassign",
            headers=self.logged_in_headers(with_super_admin_user),
            json={"group_id": group.id},
        )
        assert response.status_code == 200
        result = response.json()
        assert result["lane_group"]["id"] == group.id
