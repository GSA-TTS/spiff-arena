"""Transform task data fields into the upsert_context shape for KKV data store writes."""

import logging
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

logger = logging.getLogger(__name__)


class TransformTaskDataToDataStore(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return (
            "Reads specified fields from task data and returns an upsert_context dict "
            "ready for the data store write subprocess. Values are passed through as-is "
            "from task data (no unwrapping). Accepts field_names as a list of strings, "
            "a dict mapping task_data_key to store_name, or a single string. "
            "Skips None values by default."
        )

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        # --- Parse arguments ---
        if not args:
            raise ValueError(
                "transform_task_data_to_data_store requires at least 2 arguments: "
                "field_names (str | list | dict) and key_values (list[str])."
            )

        field_names_arg = args[0]
        key_values = args[1] if len(args) > 1 else kwargs.get("key_values")
        include_nulls = kwargs.get("include_nulls", False)

        if key_values is None:
            raise ValueError(
                "transform_task_data_to_data_store requires key_values as the second argument or as a keyword argument."
            )

        # --- Normalize field_names into a list of (task_data_key, store_name) pairs ---
        if isinstance(field_names_arg, str):
            field_pairs = [(field_names_arg, field_names_arg)]
        elif isinstance(field_names_arg, dict):
            # dict maps task_data_key -> store_name
            field_pairs = list(field_names_arg.items())
        elif isinstance(field_names_arg, list | tuple):
            field_pairs = [(name, name) for name in field_names_arg]
        else:
            raise ValueError(f"field_names must be a str, list, or dict, got {type(field_names_arg).__name__}")

        # --- Get task data ---
        task = script_attributes_context.task
        if task is None:
            return {"data": [], "key": key_values}

        task_data = task.data or {}

        # --- Build vars_array ---
        vars_array: list[dict[str, Any]] = []

        for task_key, store_name in field_pairs:
            if task_key not in task_data:
                if include_nulls:
                    vars_array.append({"name": store_name, "value": None})
                continue

            raw = task_data[task_key]

            if raw is None and not include_nulls:
                continue

            vars_array.append({"name": store_name, "value": raw})

        result = {"data": vars_array, "key": key_values}

        if kwargs.get("debug", False):
            logger.info("transform_task_data_to_data_store result: %s", result)

        return result
