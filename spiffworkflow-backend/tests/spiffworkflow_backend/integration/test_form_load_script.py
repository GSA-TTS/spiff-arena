from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestFormLoadScript(BaseTest):
    def _setup_and_run_to_manual_task(
        self,
        client: TestClient,
        with_super_admin_user: UserModel,
        bpmn_file_location: str,
    ) -> tuple[int, str]:
        """Create process instance and run it to the manual task. Returns (process_instance_id, task_guid)."""
        process_model = self.create_group_and_model_with_bpmn(
            client,
            with_super_admin_user,
            process_group_id="test_group",
            process_model_id=bpmn_file_location,
            bpmn_file_location=bpmn_file_location,
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.status_code == 201
        process_instance_id = response.json()["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=headers,
        )
        assert response.status_code == 200

        human_tasks = db.session.query(HumanTaskModel).filter(HumanTaskModel.process_instance_id == process_instance_id).all()
        assert len(human_tasks) == 1
        task_guid = human_tasks[0].task_id

        return process_instance_id, task_guid

    def test_form_load_script_executes_on_task_show(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Form load script should execute when fetching a task with with_form_data=true."""
        process_instance_id, task_guid = self._setup_and_run_to_manual_task(
            client, with_super_admin_user, "form_load_script"
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}?with_form_data=true",
            headers=headers,
        )
        assert response.status_code == 200
        task_data = response.json()["data"]

        # The form load script increments counter from 0 to 1
        assert task_data["counter"] == 1
        assert task_data["greeting"] == "hello"

    def test_form_load_script_runs_on_each_fetch(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Form load script should run each time the task is fetched, incrementing the counter."""
        process_instance_id, task_guid = self._setup_and_run_to_manual_task(
            client, with_super_admin_user, "form_load_script"
        )

        headers = self.logged_in_headers(with_super_admin_user)

        # First fetch: counter goes from 0 to 1
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}?with_form_data=true",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["counter"] == 1

        # Second fetch: counter goes from 1 to 2 (persisted from first fetch)
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}?with_form_data=true",
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["data"]["counter"] == 2

    def test_form_load_script_does_not_run_without_form_data(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """Form load script should NOT execute when with_form_data is not set."""
        process_instance_id, task_guid = self._setup_and_run_to_manual_task(
            client, with_super_admin_user, "form_load_script"
        )

        headers = self.logged_in_headers(with_super_admin_user)

        # Fetch without with_form_data — script should not run
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}",
            headers=headers,
        )
        assert response.status_code == 200
        # Data is not included in the response without with_form_data
        assert response.json().get("data") is None

    def test_form_load_script_error_returns_original_data(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        """When the form load script has an error, the original task data should be returned."""
        process_instance_id, task_guid = self._setup_and_run_to_manual_task(
            client, with_super_admin_user, "form_load_script_error"
        )

        headers = self.logged_in_headers(with_super_admin_user)
        response = client.get(
            f"/v1.0/tasks/{process_instance_id}/{task_guid}?with_form_data=true",
            headers=headers,
        )
        assert response.status_code == 200
        task_data = response.json()["data"]

        # The script has an error, so original data should be preserved
        assert task_data["my_var"] == "original_value"
