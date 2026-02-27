import json

from flask import g
from flask.app import Flask

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.task import TaskModel
from spiffworkflow_backend.scripts.get_users_assigned_to_task import GetUsersAssignedToTask
from tests.spiffworkflow_backend.helpers.base_test import BaseTest


class TestGetUsersAssignedToTask(BaseTest):
    def test_get_users_assigned_to_task(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        # Create 3 users, and set g.user
        testuser1 = self.find_or_create_user("testuser1")
        testuser2 = self.find_or_create_user("testuser2")
        testuser3 = self.find_or_create_user("testuser3")
        db.session.add_all([testuser1, testuser2, testuser3])
        db.session.commit()
        g.user = testuser1

        # Create a TaskModel + 2 HumanTaskModel rows tied to it
        task_guid = "00000000-0000-0000-0000-000000000001"
        process_instance_id = 123
        bpmn_process_id = 1
        task_definition_id = 1

        task_model = TaskModel(
            guid=task_guid,
            bpmn_process_id=bpmn_process_id,
            process_instance_id=process_instance_id,
            task_definition_id=task_definition_id,
            state="READY",
            properties_json={"last_state_change": 0, "state": 0, "task_spec": "UserTask1", "workflow_name": "wf"},
            json_data_hash="json_hash",
            python_env_data_hash="py_hash",
        )
        db.session.add(task_model)
        db.session.commit()

        humantask1 = HumanTaskModel(
            process_instance_id=process_instance_id,
            lane_assignment_id=None,
            completed_by_user_id=None,
            actual_owner_id=testuser1.id,
            form_file_name=None,
            ui_form_file_name=None,
            updated_at_in_seconds=0,
            created_at_in_seconds=0,
            task_guid=task_guid,
            task_id=task_guid,
            task_name="task_name_1",
            task_title="Task Title 1",
            task_type="User Task",
            task_status="READY",
            process_model_display_name="pm",
            bpmn_process_identifier="bpmn",
            lane_name=None,
            json_metadata=None,
            completed=False,
        )
        humantask2 = HumanTaskModel(
            process_instance_id=process_instance_id,
            lane_assignment_id=None,
            completed_by_user_id=None,
            actual_owner_id=testuser1.id,
            form_file_name=None,
            ui_form_file_name=None,
            updated_at_in_seconds=0,
            created_at_in_seconds=0,
            task_guid=task_guid,
            task_id=task_guid,
            task_name="task_name_2",
            task_title="Task Title 2",
            task_type="User Task",
            task_status="READY",
            process_model_display_name="pm",
            bpmn_process_identifier="bpmn",
            lane_name=None,
            json_metadata=None,
            completed=False,
        )
        db.session.add_all([humantask1, humantask2])
        db.session.commit()

        # Assign users
        db.session.add_all(
            [
                HumanTaskUserModel(human_task_id=humantask1.id, user_id=testuser1.id, added_by="manual"),
                HumanTaskUserModel(human_task_id=humantask1.id, user_id=testuser2.id, added_by="manual"),
            ]
        )
        # humantask2: user2 + user3 (user2 duplicates across humantask1/humantask2; script should dedupe)
        db.session.add_all(
            [
                HumanTaskUserModel(human_task_id=humantask2.id, user_id=testuser2.id, added_by="manual"),
                HumanTaskUserModel(human_task_id=humantask2.id, user_id=testuser3.id, added_by="manual"),
            ]
        )
        db.session.commit()

        # Build a lightweight "task" object that looks like what ScriptAttributesContext expects:
        # it just needs a .human_tasks attribute.
        class FakeSpiffTask:
            def __init__(self, human_tasks):
                self.human_tasks = human_tasks

        spiff_task = FakeSpiffTask([humantask1, humantask2])

        script_attributes_context = ScriptAttributesContext(
            task=spiff_task,
            environment_identifier="testing",
            process_instance_id=process_instance_id,
            process_model_identifier="test_process_model",
        )

        result = GetUsersAssignedToTask().run(script_attributes_context)

        # Should return all assigned usernames, deduped, sorted
        assert result == ["testuser1", "testuser2", "testuser3"]
        json.dumps(result)

    def test_get_users_assigned_to_task_returns_empty_if_no_task(
        self,
        app: Flask,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        script_attributes_context = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="test_process_model",
        )
        result = GetUsersAssignedToTask().run(script_attributes_context)
        assert result == []
        json.dumps(result)
