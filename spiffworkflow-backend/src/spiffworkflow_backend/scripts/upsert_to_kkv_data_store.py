"""Upsert vars_array entries into a KKV data store by name, returning the write-back dict.

Usage in BPMN script tasks:

    # Inline direct write (replaces ~15 lines of holder read/upsert/write):
    decision_payloads = upsert_to_kkv_data_store(
        decision_payloads, vars_array, process_id, current_de_process_model
    )

    # Works with any KKV store:
    management_objects = upsert_to_kkv_data_store(
        management_objects, vars_array, process_model_id, specific_key
    )

    # Combined with transform_task_data_to_data_store:
    ctx = transform_task_data_to_data_store("exclusionsText", [pid, model], include_nulls=True)
    decision_payloads = upsert_to_kkv_data_store(
        decision_payloads, ctx["data"], pid, model
    )
"""

import logging
from typing import Any

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.script import Script

logger = logging.getLogger(__name__)


def _upsert_by_name(holder: list[dict[str, Any]], vars_array: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Upsert items from vars_array into holder, matching by 'name' key.

    If an entry with the same name already exists in holder, it is replaced.
    Otherwise, the new entry is appended.
    """
    index: dict[str, int] = {str(it["name"]): i for i, it in enumerate(holder) if "name" in it}
    for item in vars_array:
        name = item.get("name")
        if not name:
            continue
        entry = {"name": name, "value": item.get("value")}
        if name in index:
            holder[index[name]] = entry
        else:
            index[name] = len(holder)
            holder.append(entry)
    return holder


class UpsertToKkvDataStore(Script):
    @staticmethod
    def requires_privileged_permissions() -> bool:
        """We have deemed this function safe to run without elevated permissions."""
        return False

    def get_description(self) -> str:
        return (
            "Reads the current holder from a KKV data store, upserts vars_array entries "
            "by name, and returns the write-back dict for assignment. "
            "Args: data_store_reader (callable), vars_array (list), key1, key2."
        )

    def run(
        self,
        script_attributes_context: ScriptAttributesContext,
        *args: Any,
        **kwargs: Any,
    ) -> Any:
        if len(args) < 4:
            raise ValueError("upsert_to_kkv_data_store requires 4 arguments: data_store_reader, vars_array, key1, key2.")

        data_store_reader = args[0]
        vars_array = args[1]
        key1 = args[2]
        key2 = args[3]

        if not callable(data_store_reader):
            raise ValueError(f"First argument must be a callable data store reader, got {type(data_store_reader).__name__}.")

        if not isinstance(vars_array, list | tuple):
            raise ValueError(f"vars_array must be a list, got {type(vars_array).__name__}.")

        # 1) Read the current bucket from the data store
        holder = data_store_reader(key1, key2)
        if holder is None or not isinstance(holder, list):
            holder = []

        # 2) Upsert vars_array into holder by name
        holder = _upsert_by_name(holder, list(vars_array))

        # 3) Return the write-back dict for assignment
        result = {key1: {key2: holder}}

        if kwargs.get("debug", False):
            logger.info("upsert_to_kkv_data_store result: %s", result)

        return result
