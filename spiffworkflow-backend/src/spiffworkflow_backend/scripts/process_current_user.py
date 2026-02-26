from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.get_current_user import GetCurrentUser
from spiffworkflow_backend.scripts.script import Script


class ProcessCurrentUser(Script):
    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        current_user = GetCurrentUser().run(script_attributes_context)
        if current_user is not None:
            return current_user
        else:
            return {"user": None}
