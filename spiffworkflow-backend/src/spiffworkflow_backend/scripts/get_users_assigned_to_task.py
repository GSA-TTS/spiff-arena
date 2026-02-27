"""Get users assigned to task."""

from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.task import TaskModel

class GetUsersAssignedToTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return all users assigned to a task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        spiff_task = script_attributes_context.task
        if not spiff_task:
            return []

        task_guid = getattr(spiff_task, "guid", None)
        if not task_guid:
            return []

        query = (
            db.session.query(UserModel.username)
            .join(HumanTaskUserModel, HumanTaskUserModel.user_id == UserModel.id)
            .join(HumanTaskModel, HumanTaskModel.id == HumanTaskUserModel.human_task_id)
            .filter(HumanTaskModel.task_guid == task_guid)
            .distinct()
        )

        usernames = [row[0] for row in query.all()]
        return sorted(usernames)
