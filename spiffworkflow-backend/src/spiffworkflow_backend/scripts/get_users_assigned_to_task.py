"""Get users assigned to task."""

from typing import Any

from flask import g

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script


class GetUsersAssignedToTask(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Return all users assigned to a task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        default_value: list[str] = []

        spiff_task = script_attributes_context.task
        if not spiff_task:
            return default_value

        human_tasks = getattr(spiff_task, "human_tasks", None)
        if not human_tasks:
            return default_value

        # Collect usernames from all potential owners on all human_task rows
        usernames: set[str] = set()
        for ht in human_tasks:
            for user in getattr(ht, "potential_owners", []) or []:
                username = getattr(user, "username", None)
                if username:
                    usernames.add(username)

        return sorted(usernames)
