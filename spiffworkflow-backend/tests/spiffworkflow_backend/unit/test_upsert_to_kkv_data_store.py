from dataclasses import dataclass
from typing import Any
from typing import cast

import pytest
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.upsert_to_kkv_data_store import UpsertToKkvDataStore
from spiffworkflow_backend.scripts.upsert_to_kkv_data_store import _upsert_by_name


@dataclass
class MockTask:
    data: dict


def _ctx() -> ScriptAttributesContext:
    return ScriptAttributesContext(
        task=cast(SpiffTask, MockTask({})),
        environment_identifier="testing",
        process_instance_id=1,
        process_model_identifier="my_test",
    )


def _make_reader(store: dict[str, dict[str, list[dict[str, Any]]]]) -> Any:
    """Create a mock KKV data store reader callable."""

    def reader(key1: str, key2: str) -> list[dict[str, Any]] | None:
        return store.get(key1, {}).get(key2)

    return reader


def _run(
    reader: Any,
    vars_array: list[dict[str, Any]],
    key1: str,
    key2: str,
) -> dict[str, Any]:
    result: dict[str, Any] = UpsertToKkvDataStore().run(_ctx(), reader, vars_array, key1, key2)
    return result


# ---------------------------------------------------------------------------
# _upsert_by_name (standalone function)
# ---------------------------------------------------------------------------
class TestUpsertByName:
    def test_append_to_empty(self) -> None:
        holder: list[dict[str, Any]] = []
        result = _upsert_by_name(holder, [{"name": "a", "value": 1}])
        assert result == [{"name": "a", "value": 1}]

    def test_replace_existing(self) -> None:
        holder = [{"name": "a", "value": "old"}, {"name": "b", "value": "keep"}]
        result = _upsert_by_name(holder, [{"name": "a", "value": "new"}])
        assert result == [{"name": "a", "value": "new"}, {"name": "b", "value": "keep"}]

    def test_mixed_upsert_and_append(self) -> None:
        holder = [{"name": "a", "value": 1}]
        result = _upsert_by_name(
            holder,
            [{"name": "a", "value": 2}, {"name": "b", "value": 3}],
        )
        assert result == [{"name": "a", "value": 2}, {"name": "b", "value": 3}]

    def test_skip_entries_without_name(self) -> None:
        holder: list[dict[str, Any]] = []
        result = _upsert_by_name(holder, [{"value": "no_name"}, {"name": "a", "value": 1}])
        assert result == [{"name": "a", "value": 1}]

    def test_preserves_holder_order(self) -> None:
        holder = [
            {"name": "x", "value": 1},
            {"name": "y", "value": 2},
            {"name": "z", "value": 3},
        ]
        result = _upsert_by_name(holder, [{"name": "y", "value": "updated"}])
        assert result[0]["name"] == "x"
        assert result[1] == {"name": "y", "value": "updated"}
        assert result[2]["name"] == "z"


# ---------------------------------------------------------------------------
# UpsertToKkvDataStore.run — end-to-end
# ---------------------------------------------------------------------------
class TestUpsertToKkvDataStore:
    def test_upsert_into_empty_store(self) -> None:
        reader = _make_reader({})
        result = _run(reader, [{"name": "field1", "value": "val1"}], "pid", "model")
        assert result == {"pid": {"model": [{"name": "field1", "value": "val1"}]}}

    def test_upsert_into_none_holder(self) -> None:
        """Store returns None for the bucket — should initialize empty."""
        reader = _make_reader({"pid": {"model": None}})  # type: ignore
        result = _run(reader, [{"name": "a", "value": 1}], "pid", "model")
        assert result == {"pid": {"model": [{"name": "a", "value": 1}]}}

    def test_upsert_replaces_existing_entry(self) -> None:
        reader = _make_reader(
            {
                "pid": {
                    "model": [
                        {"name": "a", "value": "old"},
                        {"name": "b", "value": "keep"},
                    ]
                }
            }
        )
        result = _run(reader, [{"name": "a", "value": "new"}], "pid", "model")
        holder = result["pid"]["model"]
        assert holder[0] == {"name": "a", "value": "new"}
        assert holder[1] == {"name": "b", "value": "keep"}

    def test_upsert_appends_new_entries(self) -> None:
        reader = _make_reader({"pid": {"model": [{"name": "existing", "value": 1}]}})
        result = _run(reader, [{"name": "new_field", "value": 2}], "pid", "model")
        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {"name": "existing", "value": 1}
        assert holder[1] == {"name": "new_field", "value": 2}

    def test_multiple_fields_upsert(self) -> None:
        """Simulates the EC forced_vars pattern with multiple fields."""
        reader = _make_reader({"pid": {"model": [{"name": "publicHealthImpacts", "value": "old"}]}})
        vars_array: list[dict[str, Any]] = [
            {"name": "publicHealthImpacts", "value": "updated"},
            {"name": "naturalResourcesImpacts", "value": "new"},
            {"name": "controversialEffects", "value": None},
        ]
        result = _run(reader, vars_array, "pid", "model")
        holder = result["pid"]["model"]
        assert len(holder) == 3
        assert holder[0] == {"name": "publicHealthImpacts", "value": "updated"}
        assert holder[1] == {"name": "naturalResourcesImpacts", "value": "new"}
        assert holder[2] == {"name": "controversialEffects", "value": None}

    def test_exclusions_text_pattern(self) -> None:
        """Simulates the single-field exclusionsText inline write."""
        reader = _make_reader(
            {
                "pid": {
                    "model": [
                        {"name": "exclusionsText", "value": "old text"},
                        {"name": "otherField", "value": "keep"},
                    ]
                }
            }
        )
        result = _run(
            reader,
            [{"name": "exclusionsText", "value": "new CE text"}],
            "pid",
            "model",
        )
        holder = result["pid"]["model"]
        assert holder[0] == {"name": "exclusionsText", "value": "new CE text"}
        assert holder[1] == {"name": "otherField", "value": "keep"}

    def test_return_dict_structure(self) -> None:
        """Confirms the return dict is ready for KKV assignment."""
        reader = _make_reader({})
        result = _run(reader, [{"name": "a", "value": 1}], "process_123", "BLM-CE")
        assert "process_123" in result
        assert "BLM-CE" in result["process_123"]
        assert isinstance(result["process_123"]["BLM-CE"], list)

    def test_empty_vars_array_reads_and_returns(self) -> None:
        existing = [{"name": "keep", "value": "me"}]
        reader = _make_reader({"pid": {"model": existing}})
        result = _run(reader, [], "pid", "model")
        assert result["pid"]["model"] == existing


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------
class TestUpsertErrors:
    def test_not_enough_args_raises(self) -> None:
        with pytest.raises(ValueError, match="requires 4 arguments"):
            UpsertToKkvDataStore().run(_ctx(), "only_one")

    def test_non_callable_reader_raises(self) -> None:
        with pytest.raises(ValueError, match="callable data store reader"):
            _run("not_a_function", [{"name": "a", "value": 1}], "pid", "model")

    def test_non_list_vars_array_raises(self) -> None:
        reader = _make_reader({})
        with pytest.raises(ValueError, match="vars_array must be a list"):
            _run(reader, "not_a_list", "pid", "model")  # type: ignore


# ---------------------------------------------------------------------------
# Integration with transform_task_data_to_data_store output
# ---------------------------------------------------------------------------
class TestIntegrationWithTransform:
    """Tests that the output of transform_task_data_to_data_store feeds correctly
    into upsert_to_kkv_data_store."""

    def test_transform_output_feeds_into_upsert(self) -> None:
        """Simulates the combined pipeline."""
        # Simulate transform output
        transform_result: dict[str, Any] = {
            "data": [
                {"name": "exclusionsText", "value": "CE text here"},
            ],
            "key": ["process_id_123", "BLM-MOAB-CE"],
        }
        reader = _make_reader({})
        result = _run(
            reader,
            transform_result["data"],
            transform_result["key"][0],
            transform_result["key"][1],
        )
        assert result == {"process_id_123": {"BLM-MOAB-CE": [{"name": "exclusionsText", "value": "CE text here"}]}}

    def test_nepareport_remapping_pipeline(self) -> None:
        """Simulates the nepareport/ipac_report dict-remapping + upsert pipeline."""
        # transform_task_data_to_data_store({"nepareport": "nepareport", "ipac_report": "ipacreport"}, ...)
        # would produce:
        transform_result: dict[str, Any] = {
            "data": [
                {"name": "nepareport", "value": {"report_data": "nepa"}},
                {"name": "ipacreport", "value": {"report_data": "ipac"}},
            ],
            "key": ["pid", "model"],
        }
        reader = _make_reader({"pid": {"model": [{"name": "existing", "value": "keep"}]}})
        result = _run(reader, transform_result["data"], "pid", "model")
        holder = result["pid"]["model"]
        assert len(holder) == 3
        assert holder[0] == {"name": "existing", "value": "keep"}
        assert holder[1] == {"name": "nepareport", "value": {"report_data": "nepa"}}
        assert holder[2] == {"name": "ipacreport", "value": {"report_data": "ipac"}}
