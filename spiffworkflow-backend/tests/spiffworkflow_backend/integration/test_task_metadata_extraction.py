from flask import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestTaskMetadataExtraction(BaseTest):
    def _create_model_and_run(
        self,
        client: TestClient,
        user: UserModel,
        bpmn_file_location: str,
        task_metadata_extraction_paths: list[dict[str, str]] | None = None,
    ) -> int:
        process_group_id = "test_group"
        process_model_id = bpmn_file_location

        process_model = self.create_group_and_model_with_bpmn(
            client,
            user,
            process_group_id=process_group_id,
            process_model_id=process_model_id,
            bpmn_file_location=bpmn_file_location,
        )

        if task_metadata_extraction_paths is not None:
            process_model.task_metadata_extraction_paths = task_metadata_extraction_paths
            ProcessModelService.save_process_model(process_model)

        headers = self.logged_in_headers(user)
        response = self.create_process_instance_from_process_model_id_with_api(client, process_model.id, headers)
        assert response.status_code == 201
        process_instance_id = response.json()["id"]

        response = client.post(
            f"/v1.0/process-instances/{self.modify_process_identifier_for_path_param(process_model.id)}/{process_instance_id}/run",
            headers=headers,
        )
        assert response.status_code == 200
        return process_instance_id

    def test_model_level_extraction_populates_json_metadata(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_instance_id = self._create_model_and_run(
            client,
            with_super_admin_user,
            bpmn_file_location="task_metadata_extraction",
            task_metadata_extraction_paths=[
                {"key": "customer", "path": "customer_name"},
                {"key": "order", "path": "order_id"},
                {"key": "amount", "path": "details.amount"},
            ],
        )

        human_tasks = db.session.query(HumanTaskModel).filter(
            HumanTaskModel.process_instance_id == process_instance_id
        ).all()
        assert len(human_tasks) == 1
        human_task = human_tasks[0]

        assert human_task.json_metadata is not None
        assert human_task.json_metadata["customer"] == "Jane Doe"
        assert human_task.json_metadata["order"] == "ORD-12345"
        assert human_task.json_metadata["amount"] == 99.99

    def test_per_task_metadata_overrides_model_level(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_instance_id = self._create_model_and_run(
            client,
            with_super_admin_user,
            bpmn_file_location="task_metadata_extraction_with_override",
            task_metadata_extraction_paths=[
                {"key": "customer", "path": "customer_name"},
                {"key": "priority", "path": "priority"},
            ],
        )

        human_tasks = db.session.query(HumanTaskModel).filter(
            HumanTaskModel.process_instance_id == process_instance_id
        ).all()
        assert len(human_tasks) == 1
        human_task = human_tasks[0]

        assert human_task.json_metadata is not None
        # model-level extraction should be present
        assert human_task.json_metadata["customer"] == "Jane Doe"
        # per-task taskMetadataValues should override model-level for same key
        assert human_task.json_metadata["priority"] == "overridden_priority"
        # per-task only key should be present
        assert human_task.json_metadata["task_only_key"] == "task_only_value"

    def test_missing_paths_produce_no_entry(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_instance_id = self._create_model_and_run(
            client,
            with_super_admin_user,
            bpmn_file_location="task_metadata_extraction",
            task_metadata_extraction_paths=[
                {"key": "customer", "path": "customer_name"},
                {"key": "nonexistent", "path": "does_not_exist"},
                {"key": "deep_missing", "path": "details.missing.nested"},
            ],
        )

        human_tasks = db.session.query(HumanTaskModel).filter(
            HumanTaskModel.process_instance_id == process_instance_id
        ).all()
        assert len(human_tasks) == 1
        human_task = human_tasks[0]

        assert human_task.json_metadata is not None
        assert human_task.json_metadata["customer"] == "Jane Doe"
        # Missing paths should not produce entries (filtered out because value is None)
        assert "nonexistent" not in human_task.json_metadata
        assert "deep_missing" not in human_task.json_metadata

    def test_no_extraction_paths_leaves_metadata_empty(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
        with_super_admin_user: UserModel,
    ) -> None:
        process_instance_id = self._create_model_and_run(
            client,
            with_super_admin_user,
            bpmn_file_location="task_metadata_extraction",
            task_metadata_extraction_paths=None,
        )

        human_tasks = db.session.query(HumanTaskModel).filter(
            HumanTaskModel.process_instance_id == process_instance_id
        ).all()
        assert len(human_tasks) == 1
        human_task = human_tasks[0]

        assert human_task.json_metadata == {}
