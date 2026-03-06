from dataclasses import dataclass
from typing import Any
from typing import cast

import pytest
from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.transform_task_data_to_data_store import TransformTaskDataToDataStore


@dataclass
class MockTask:
    data: dict


def _ctx(task_data: dict) -> ScriptAttributesContext:
    return ScriptAttributesContext(
        task=cast(SpiffTask, MockTask(task_data)),
        environment_identifier="testing",
        process_instance_id=1,
        process_model_identifier="my_test",
    )


def _run(task_data: dict, field_names: Any, key_values: list[str], **kwargs: Any) -> dict[str, Any]:
    result: dict[str, Any] = TransformTaskDataToDataStore().run(_ctx(task_data), field_names, key_values, **kwargs)
    return result


# ---------------------------------------------------------------------------
# TransformTaskDataToDataStore.run — field_names variations
# ---------------------------------------------------------------------------
class TestTransformFieldNames:
    def test_list_of_strings(self) -> None:
        result = _run(
            {"field1": "val1", "field2": {"value": "val2"}},
            ["field1", "field2"],
            ["MODEL", "PID"],
        )
        assert result["key"] == ["MODEL", "PID"]
        assert result["data"] == [
            {"name": "field1", "value": "val1"},
            {"name": "field2", "value": {"value": "val2"}},
        ]

    def test_single_string(self) -> None:
        result = _run({"exclusionsText": "hello"}, "exclusionsText", ["M", "P"])
        assert result["data"] == [{"name": "exclusionsText", "value": "hello"}]

    def test_dict_remapping(self) -> None:
        result = _run(
            {"ipac_report": {"value": "data"}},
            {"ipac_report": "ipacreport"},
            ["M", "P"],
        )
        assert result["data"] == [{"name": "ipacreport", "value": {"value": "data"}}]


# ---------------------------------------------------------------------------
# Null handling
# ---------------------------------------------------------------------------
class TestNullHandling:
    def test_none_values_skipped_by_default(self) -> None:
        result = _run({"a": None, "b": "yes"}, ["a", "b"], ["M", "P"])
        assert len(result["data"]) == 1
        assert result["data"][0]["name"] == "b"

    def test_missing_fields_skipped_by_default(self) -> None:
        result = _run({"a": "yes"}, ["a", "b", "c"], ["M", "P"])
        assert len(result["data"]) == 1

    def test_include_nulls_keeps_none_values(self) -> None:
        result = _run({"a": None, "b": "yes"}, ["a", "b"], ["M", "P"], include_nulls=True)
        assert len(result["data"]) == 2
        assert result["data"][0] == {"name": "a", "value": None}

    def test_include_nulls_adds_missing_fields(self) -> None:
        result = _run({"b": "yes"}, ["b", "missing"], ["M", "P"], include_nulls=True)
        assert len(result["data"]) == 2
        assert result["data"][1] == {"name": "missing", "value": None}


# ---------------------------------------------------------------------------
# Raw value pass-through (values are NOT unwrapped)
# ---------------------------------------------------------------------------
class TestRawValuePassThrough:
    def test_container_dict_passed_as_is(self) -> None:
        """EC fields like {"value": "text", "comment": {}} must pass through intact."""
        result = _run(
            {
                "publicHealthImpacts": {
                    "value": "Impact text",
                    "comment": {"saved": True},
                }
            },
            ["publicHealthImpacts"],
            ["M", "P"],
        )
        entry = result["data"][0]
        assert entry["name"] == "publicHealthImpacts"
        assert entry["value"] == {"value": "Impact text", "comment": {"saved": True}}

    def test_nested_value_dict_not_unwrapped(self) -> None:
        """A dict with a 'value' key should NOT be unwrapped — stored as-is."""
        result = _run(
            {"lupDecisions": {"value": {"decisions": []}, "comment": {"saved": True}}},
            ["lupDecisions"],
            ["M", "P"],
        )
        entry = result["data"][0]
        assert entry["name"] == "lupDecisions"
        assert entry["value"] == {
            "value": {"decisions": []},
            "comment": {"saved": True},
        }

    def test_double_nested_value_passed_through(self) -> None:
        """Double-nested {"value": {"value": "actual"}} is NOT unwrapped."""
        result = _run({"field": {"value": {"value": "actual"}}}, ["field"], ["M", "P"])
        assert result["data"][0]["value"] == {"value": {"value": "actual"}}

    def test_multiple_ec_fields_preserve_containers(self) -> None:
        """Multiple EC fields all keep their container shape."""
        task_data = {
            "publicHealthImpacts": {"value": "text1", "comment": {}},
            "naturalResourcesImpacts": {"value": "text2", "comment": {}},
            "categoricalExclusionJustification": {
                "value": "justification",
                "comment": {},
            },
        }
        result = _run(
            task_data,
            [
                "publicHealthImpacts",
                "naturalResourcesImpacts",
                "categoricalExclusionJustification",
            ],
            ["BLM-MOAB-CE", "16"],
            include_nulls=True,
        )
        for entry in result["data"]:
            assert isinstance(entry["value"], dict)
            assert "value" in entry["value"]
            assert "comment" in entry["value"]


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------
class TestEdgeCases:
    def test_no_task_returns_empty_data(self) -> None:
        ctx = ScriptAttributesContext(
            task=None,
            environment_identifier="testing",
            process_instance_id=1,
            process_model_identifier="my_test",
        )
        result = TransformTaskDataToDataStore().run(ctx, ["a"], ["M", "P"])
        assert result == {"data": [], "key": ["M", "P"]}

    def test_empty_task_data(self) -> None:
        result = _run({}, ["a", "b"], ["M", "P"])
        assert result["data"] == []

    def test_scalar_values_passed_through(self) -> None:
        result = _run({"count": 42, "name": "test"}, ["count", "name"], ["M", "P"])
        assert result["data"][0] == {"name": "count", "value": 42}
        assert result["data"][1] == {"name": "name", "value": "test"}

    def test_dict_without_value_key_passed_as_is(self) -> None:
        result = _run({"config": {"setting": True}}, ["config"], ["M", "P"])
        assert result["data"][0]["value"] == {"setting": True}

    def test_invalid_field_names_type_raises(self) -> None:
        with pytest.raises(ValueError, match="field_names must be"):
            _run({"a": 1}, 123, ["M", "P"])

    def test_missing_key_values_raises(self) -> None:
        with pytest.raises(ValueError, match="key_values"):
            TransformTaskDataToDataStore().run(_ctx({"a": 1}), ["a"])
