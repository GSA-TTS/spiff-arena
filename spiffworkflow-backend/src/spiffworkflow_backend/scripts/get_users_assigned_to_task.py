"""Get users assigned to task."""

from typing import Any

from sqlalchemy import select

from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.scripts.script import Script


class GetUsersAssignedToTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return all users assigned to a task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        task_guid = kwargs["task_guid"]
        if not task_guid:
            return []

        stmt = (
            select(UserModel.username)
            .select_from(HumanTaskModel)
            .join(HumanTaskModel.potential_owners)
            .where(HumanTaskModel.task_guid == task_guid)
            .distinct()
        )

        usernames = db.session.execute(stmt).scalars().all()
        return sorted(usernames)
