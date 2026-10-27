from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script
from spiffworkflow_backend.services.bpmn_process_service import BpmnProcessService


class GetCurrentTaskInfo(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return """Returns the information about the current task."""

    def run(self, script_attributes_context: ScriptAttributesContext, *_args: Any, **kwargs: Any) -> Any:
        task_dict = BpmnProcessService.serializer.to_dict(script_attributes_context.task)
        task_dict.pop("data")
        # Delta also contains task data, not metadata. RestrictedPython >= 8.2 added Ellipsis to
        # safe_builtins, which Spiff's TaskConverter.to_dict() picks up as a "task data" key
        # (__builtins__) because this script runs mid-execution, while the script engine's
        # injected __builtins__ is still present in task.data. That makes the
        # delta.updates.__builtins__ dict (containing the non-JSON-serializable Ellipsis sentinel)
        # show up here and blow up JSON serialization downstream. Drop delta too, since it isn't
        # metadata we want to expose anyway.
        # Note: RestrictedPython >= 8.2 also allows scripts to assign Ellipsis directly to task
        # data (`x = ...`), which is a separate, broader risk tracked in
        # https://github.com/GSA-TTS/spiff-arena/issues/113 and not fixed by this change.
        task_dict.pop("delta", None)
        return task_dict
