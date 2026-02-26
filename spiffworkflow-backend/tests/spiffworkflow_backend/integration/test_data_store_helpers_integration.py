"""Integration tests for transform_task_data_to_data_store + upsert_to_kkv_data_store.

These tests verify the two helpers work correctly together in realistic BPMN
pipeline scenarios — mirroring the patterns we replaced in doe-ce, fra-ce,
baseline-ce, epa-ce, short-ce, and dhs BPMN files.
"""

from dataclasses import dataclass
from typing import Any
from typing import cast

from SpiffWorkflow.task import Task as SpiffTask  # type: ignore

from spiffworkflow_backend.models.script_attributes_context import ScriptAttributesContext
from spiffworkflow_backend.scripts.transform_task_data_to_data_store import TransformTaskDataToDataStore
from spiffworkflow_backend.scripts.upsert_to_kkv_data_store import UpsertToKkvDataStore


# ---------------------------------------------------------------------------
# Test infrastructure
# ---------------------------------------------------------------------------
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


def _make_reader(store: dict[str, dict[str, list[dict[str, Any]]]]) -> Any:
    """Create a mock KKV reader callable matching KKVDataStore.get behavior."""

    def reader(key1: str, key2: str) -> list[dict[str, Any]] | None:
        return store.get(key1, {}).get(key2)

    return reader


def _transform(task_data: dict, field_names: Any, key_values: list[str], **kwargs: Any) -> dict[str, Any]:
    result: dict[str, Any] = TransformTaskDataToDataStore().run(_ctx(task_data), field_names, key_values, **kwargs)
    return result


def _upsert(reader: Any, vars_array: list[dict[str, Any]], key1: str, key2: str) -> dict[str, Any]:
    result: dict[str, Any] = UpsertToKkvDataStore().run(_ctx({}), reader, vars_array, key1, key2)
    return result


def _pipeline(
    task_data: dict,
    field_names: Any,
    reader: Any,
    key1: str,
    key2: str,
    **transform_kwargs: Any,
) -> dict:
    """Run the full transform → upsert pipeline, exactly as BPMN scripts do."""
    upsert_context = _transform(task_data, field_names, [key1, key2], **transform_kwargs)
    return _upsert(reader, upsert_context["data"], key1, key2)


# ---------------------------------------------------------------------------
# Pattern A1: Dynamic schema fields (hellocedata variable_names)
# ---------------------------------------------------------------------------
class TestDynamicSchemaFieldsPipeline:
    """Mirrors the A1 pattern where variable_names come from hellocedata schema."""

    def test_multiple_schema_fields_into_empty_store(self) -> None:
        variable_names = [
            "publicHealthImpacts",
            "naturalResourcesImpacts",
            "controversialEffects",
        ]
        task_data = {
            "publicHealthImpacts": "minimal impact",
            "naturalResourcesImpacts": {"value": "some impact"},
            "controversialEffects": None,
        }
        reader = _make_reader({})
        result = _pipeline(task_data, variable_names, reader, "pid_001", "BLM-MOAB-CE")

        holder = result["pid_001"]["BLM-MOAB-CE"]
        assert len(holder) == 2  # None values skipped by default
        assert holder[0] == {"name": "publicHealthImpacts", "value": "minimal impact"}
        assert holder[1] == {"name": "naturalResourcesImpacts", "value": "some impact"}

    def test_schema_fields_upsert_into_existing_store(self) -> None:
        variable_names = ["publicHealthImpacts", "naturalResourcesImpacts"]
        task_data = {
            "publicHealthImpacts": "UPDATED impact",
            "naturalResourcesImpacts": "new assessment",
        }
        reader = _make_reader(
            {
                "pid_001": {
                    "BLM-MOAB-CE": [
                        {"name": "publicHealthImpacts", "value": "old impact"},
                        {"name": "exclusionsText", "value": "keep me"},
                    ]
                }
            }
        )
        result = _pipeline(task_data, variable_names, reader, "pid_001", "BLM-MOAB-CE")

        holder = result["pid_001"]["BLM-MOAB-CE"]
        assert len(holder) == 3
        assert holder[0] == {"name": "publicHealthImpacts", "value": "UPDATED impact"}
        assert holder[1] == {"name": "exclusionsText", "value": "keep me"}
        assert holder[2] == {
            "name": "naturalResourcesImpacts",
            "value": "new assessment",
        }

    def test_nine_ec_fields_from_schema(self) -> None:
        """Simulates all 9 EC form fields from hellocedata schema."""
        variable_names = [
            "publicHealthImpacts",
            "naturalResourcesImpacts",
            "controversialEffects",
            "uncertainEffects",
            "precedentSetting",
            "cumulativeImpact",
            "historicDistrictImpact",
            "endangeredSpeciesImpact",
            "hazardousWasteImpact",
        ]
        task_data = {name: f"value_for_{name}" for name in variable_names}
        reader = _make_reader({})
        result = _pipeline(task_data, variable_names, reader, "proc_42", "DOE-CE")

        holder = result["proc_42"]["DOE-CE"]
        assert len(holder) == 9
        for i, name in enumerate(variable_names):
            assert holder[i]["name"] == name
            assert holder[i]["value"] == f"value_for_{name}"


# ---------------------------------------------------------------------------
# Pattern A2: Single field (exclusionsText)
# ---------------------------------------------------------------------------
class TestExclusionsTextPipeline:
    """Mirrors the A2 pattern: single exclusionsText field write."""

    def test_exclusions_text_into_empty_store(self) -> None:
        task_data = {"exclusionsText": "CE text content"}
        reader = _make_reader({})
        result = _pipeline(task_data, "exclusionsText", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert holder == [{"name": "exclusionsText", "value": "CE text content"}]

    def test_exclusions_text_updates_existing_entry(self) -> None:
        task_data = {"exclusionsText": "new CE text"}
        reader = _make_reader(
            {
                "pid": {
                    "model": [
                        {"name": "exclusionsText", "value": "old CE text"},
                        {"name": "otherField", "value": "untouched"},
                    ]
                }
            }
        )
        result = _pipeline(task_data, "exclusionsText", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {"name": "exclusionsText", "value": "new CE text"}
        assert holder[1] == {"name": "otherField", "value": "untouched"}

    def test_exclusions_text_with_wrapped_value(self) -> None:
        """Task data often wraps values: {"value": "actual", "comment": {...}}."""
        task_data = {
            "exclusionsText": {
                "value": "CE text from form",
                "comment": {"comment": "reviewer note", "saved": True},
            }
        }
        reader = _make_reader({})
        result = _pipeline(task_data, "exclusionsText", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 1
        assert holder[0]["name"] == "exclusionsText"
        assert holder[0]["value"] == "CE text from form"
        # comment is preserved through transform but dropped by upsert (by design)
        # since upsert only keeps name+value

    def test_exclusions_text_none_skipped(self) -> None:
        task_data = {"exclusionsText": None}
        reader = _make_reader({"pid": {"model": [{"name": "keep", "value": "me"}]}})
        result = _pipeline(task_data, "exclusionsText", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert holder == [{"name": "keep", "value": "me"}]


# ---------------------------------------------------------------------------
# Pattern A3: lupDecisions with comment
# ---------------------------------------------------------------------------
class TestLupDecisionsPipeline:
    """Mirrors the A3 pattern: lupDecisions data with comment preservation.

    In the real BPMN, the lupDecisions data is constructed with custom logic
    before being fed to upsert_to_kkv_data_store. The transform helper handles
    comment extraction.
    """

    def test_lup_decisions_with_comment_through_transform(self) -> None:
        task_data = {
            "lupDecisions": {
                "value": "Specifically provided: Environmental Assessment",
                "comment": {"comment": "Reviewer approved", "saved": True},
            }
        }
        upsert_context = _transform(task_data, "lupDecisions", ["pid", "model"])
        entry = upsert_context["data"][0]
        assert entry["name"] == "lupDecisions"
        assert entry["value"] == "Specifically provided: Environmental Assessment"
        assert entry["comment"] == {"comment": "Reviewer approved", "saved": True}

    def test_lup_decisions_manual_vars_array_with_upsert(self) -> None:
        """In the actual A3 BPMN pattern, vars_array is built manually with custom
        logic, then only the upsert portion is replaced by our helper."""
        vars_array = [
            {
                "name": "lupDecisions",
                "value": {"decisions": ["decision1", "decision2"]},
                "comment": {"comment": "", "saved": False},
            }
        ]
        reader = _make_reader({})
        result = _upsert(reader, vars_array, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 1
        # upsert_by_name keeps name + value, comment is an extra field
        assert holder[0]["name"] == "lupDecisions"
        assert holder[0]["value"] == {"decisions": ["decision1", "decision2"]}

    def test_lup_decisions_upsert_replaces_existing(self) -> None:
        vars_array = [
            {
                "name": "lupDecisions",
                "value": "Updated decisions text",
            }
        ]
        reader = _make_reader(
            {
                "pid": {
                    "model": [
                        {"name": "lupDecisions", "value": "Old decisions"},
                        {"name": "exclusionsText", "value": "keep"},
                    ]
                }
            }
        )
        result = _upsert(reader, vars_array, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {"name": "lupDecisions", "value": "Updated decisions text"}
        assert holder[1] == {"name": "exclusionsText", "value": "keep"}


# ---------------------------------------------------------------------------
# Pattern B1: nepareport only
# ---------------------------------------------------------------------------
class TestNepareportPipeline:
    """Mirrors the B1 pattern: single nepareport field with identity mapping."""

    def test_nepareport_into_empty_store(self) -> None:
        task_data = {"nepareport": {"report_data": "nepa content"}}
        reader = _make_reader({})
        result = _pipeline(task_data, "nepareport", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert holder == [{"name": "nepareport", "value": {"report_data": "nepa content"}}]

    def test_nepareport_appends_to_existing(self) -> None:
        task_data = {"nepareport": {"report_data": "nepa"}}
        reader = _make_reader({"pid": {"model": [{"name": "existingField", "value": "keep"}]}})
        result = _pipeline(task_data, "nepareport", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {"name": "existingField", "value": "keep"}
        assert holder[1] == {"name": "nepareport", "value": {"report_data": "nepa"}}


# ---------------------------------------------------------------------------
# Pattern B2: nepareport + ipac_report with dict remapping
# ---------------------------------------------------------------------------
class TestNepareportIpacPipeline:
    """Mirrors the B2 pattern: nepareport + ipac_report with key remapping."""

    def test_both_fields_present(self) -> None:
        task_data = {
            "nepareport": {"value": {"nepa": "data"}},
            "ipac_report": {"value": {"ipac": "data"}},
        }
        field_map = {"nepareport": "nepareport", "ipac_report": "ipacreport"}
        reader = _make_reader({})
        result = _pipeline(task_data, field_map, reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {"name": "nepareport", "value": {"nepa": "data"}}
        assert holder[1] == {"name": "ipacreport", "value": {"ipac": "data"}}

    def test_only_nepareport_present(self) -> None:
        task_data = {"nepareport": "nepa_data"}
        field_map = {"nepareport": "nepareport", "ipac_report": "ipacreport"}
        reader = _make_reader({})
        result = _pipeline(task_data, field_map, reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 1
        assert holder[0] == {"name": "nepareport", "value": "nepa_data"}

    def test_only_ipac_present(self) -> None:
        task_data = {"ipac_report": "ipac_data"}
        field_map = {"nepareport": "nepareport", "ipac_report": "ipacreport"}
        reader = _make_reader({})
        result = _pipeline(task_data, field_map, reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 1
        assert holder[0] == {"name": "ipacreport", "value": "ipac_data"}

    def test_remapped_fields_upsert_into_existing_store(self) -> None:
        task_data = {
            "nepareport": "updated_nepa",
            "ipac_report": "updated_ipac",
        }
        field_map = {"nepareport": "nepareport", "ipac_report": "ipacreport"}
        reader = _make_reader(
            {
                "pid": {
                    "model": [
                        {"name": "nepareport", "value": "old_nepa"},
                        {"name": "ipacreport", "value": "old_ipac"},
                        {"name": "exclusionsText", "value": "keep"},
                    ]
                }
            }
        )
        result = _pipeline(task_data, field_map, reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 3
        assert holder[0] == {"name": "nepareport", "value": "updated_nepa"}
        assert holder[1] == {"name": "ipacreport", "value": "updated_ipac"}
        assert holder[2] == {"name": "exclusionsText", "value": "keep"}


# ---------------------------------------------------------------------------
# Baseline idTeamChecklist pattern
# ---------------------------------------------------------------------------
class TestIdTeamChecklistPipeline:
    """Mirrors the baseline-ce idTeamChecklist pattern where vars_array is
    manually constructed from resources_upper before calling upsert."""

    def test_id_team_checklist_manual_vars_into_upsert(self) -> None:
        # Simulate the resource_dict computation from BPMN
        resources_upper = [{"resource1": True, "resource2": False}]
        resource_dict: dict[str, Any] = {}
        for item in resources_upper:
            if isinstance(item, dict):
                resource_dict.update(item)
        vars_array = [{"name": "idTeamChecklist", "value": resource_dict}]

        reader = _make_reader({})
        result = _upsert(reader, vars_array, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 1
        assert holder[0] == {
            "name": "idTeamChecklist",
            "value": {"resource1": True, "resource2": False},
        }

    def test_id_team_checklist_updates_existing(self) -> None:
        vars_array = [{"name": "idTeamChecklist", "value": {"resource1": True, "new": "added"}}]
        reader = _make_reader(
            {
                "pid": {
                    "model": [
                        {"name": "idTeamChecklist", "value": {"resource1": False}},
                        {"name": "otherField", "value": "keep"},
                    ]
                }
            }
        )
        result = _upsert(reader, vars_array, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {
            "name": "idTeamChecklist",
            "value": {"resource1": True, "new": "added"},
        }
        assert holder[1] == {"name": "otherField", "value": "keep"}


# ---------------------------------------------------------------------------
# Multi-step workflow simulation
# ---------------------------------------------------------------------------
class TestMultiStepWorkflow:
    """Simulates a realistic BPMN workflow where multiple script tasks write
    to the same KKV data store bucket across different steps."""

    def test_sequential_writes_accumulate(self) -> None:
        """Step 1: Write exclusionsText. Step 2: Write schema fields.
        Step 3: Write lupDecisions."""
        store: dict[str, dict[str, list[dict[str, Any]]]] = {}

        # Step 1: exclusionsText
        result = _pipeline(
            {"exclusionsText": "CE-1 exclusion text"},
            "exclusionsText",
            _make_reader(store),
            "proc_1",
            "DOE-CE",
        )
        store = result  # Simulate KKV persisting the write

        # Step 2: Schema fields
        result = _pipeline(
            {
                "publicHealthImpacts": "low",
                "naturalResourcesImpacts": "moderate",
            },
            ["publicHealthImpacts", "naturalResourcesImpacts"],
            _make_reader(store),
            "proc_1",
            "DOE-CE",
        )
        store = result

        # Step 3: lupDecisions (manual vars_array, upsert only)
        vars_array = [{"name": "lupDecisions", "value": "Decisions text here"}]
        result = _upsert(_make_reader(store), vars_array, "proc_1", "DOE-CE")
        store = result

        # Verify all three steps accumulated
        holder = store["proc_1"]["DOE-CE"]
        assert len(holder) == 4
        names = [item["name"] for item in holder]
        assert "exclusionsText" in names
        assert "publicHealthImpacts" in names
        assert "naturalResourcesImpacts" in names
        assert "lupDecisions" in names

    def test_repeated_updates_overwrite_not_duplicate(self) -> None:
        """Running the same pipeline twice for the same field should update,
        not append a duplicate."""
        store: dict[str, dict[str, list[dict[str, Any]]]] = {}

        # First write
        result = _pipeline(
            {"exclusionsText": "version 1"},
            "exclusionsText",
            _make_reader(store),
            "pid",
            "model",
        )
        store = result

        # Second write — should update, not duplicate
        result = _pipeline(
            {"exclusionsText": "version 2"},
            "exclusionsText",
            _make_reader(store),
            "pid",
            "model",
        )
        store = result

        holder = store["pid"]["model"]
        assert len(holder) == 1
        assert holder[0] == {"name": "exclusionsText", "value": "version 2"}

    def test_different_process_ids_stay_isolated(self) -> None:
        """Two different process instances writing to the same model
        should not interfere with each other."""
        store: dict[str, dict[str, list[dict[str, Any]]]] = {}

        # Process 1
        result = _pipeline(
            {"exclusionsText": "proc1 text"},
            "exclusionsText",
            _make_reader(store),
            "proc_1",
            "DOE-CE",
        )
        store.update(result)

        # Process 2
        result = _pipeline(
            {"exclusionsText": "proc2 text"},
            "exclusionsText",
            _make_reader(store),
            "proc_2",
            "DOE-CE",
        )
        store.update(result)

        assert store["proc_1"]["DOE-CE"] == [{"name": "exclusionsText", "value": "proc1 text"}]
        assert store["proc_2"]["DOE-CE"] == [{"name": "exclusionsText", "value": "proc2 text"}]

    def test_mixed_patterns_in_single_workflow(self) -> None:
        """Simulates a workflow that uses A1, A2, B2, and manual vars_array
        patterns across different script tasks."""
        store: dict[str, dict[str, list[dict[str, Any]]]] = {}
        pid, model = "workflow_99", "BASELINE-CE"

        # A2: exclusionsText
        result = _pipeline(
            {"exclusionsText": "CE text"},
            "exclusionsText",
            _make_reader(store),
            pid,
            model,
        )
        store = result

        # A1: Schema fields
        result = _pipeline(
            {"field1": "val1", "field2": "val2", "field3": "val3"},
            ["field1", "field2", "field3"],
            _make_reader(store),
            pid,
            model,
        )
        store = result

        # B2: nepareport + ipac remapping
        result = _pipeline(
            {"nepareport": "nepa_content", "ipac_report": "ipac_content"},
            {"nepareport": "nepareport", "ipac_report": "ipacreport"},
            _make_reader(store),
            pid,
            model,
        )
        store = result

        # idTeamChecklist: manual vars_array
        vars_array = [{"name": "idTeamChecklist", "value": {"r1": True}}]
        result = _upsert(_make_reader(store), vars_array, pid, model)
        store = result

        holder = store[pid][model]
        assert len(holder) == 7
        names = {item["name"] for item in holder}
        assert names == {
            "exclusionsText",
            "field1",
            "field2",
            "field3",
            "nepareport",
            "ipacreport",
            "idTeamChecklist",
        }


# ---------------------------------------------------------------------------
# Edge cases for the combined pipeline
# ---------------------------------------------------------------------------
class TestPipelineEdgeCases:
    def test_empty_task_data_no_op(self) -> None:
        """Empty task data produces empty vars_array, store is returned unchanged."""
        reader = _make_reader({"pid": {"model": [{"name": "existing", "value": "keep"}]}})
        result = _pipeline({}, ["nonexistent_field"], reader, "pid", "model")
        assert result["pid"]["model"] == [{"name": "existing", "value": "keep"}]

    def test_all_none_values_skipped(self) -> None:
        task_data = {"field1": None, "field2": None}
        reader = _make_reader({})
        result = _pipeline(task_data, ["field1", "field2"], reader, "pid", "model")
        assert result["pid"]["model"] == []

    def test_include_nulls_propagates_through_pipeline(self) -> None:
        task_data = {"field1": None, "field2": "has_value"}
        reader = _make_reader({})
        result = _pipeline(
            task_data,
            ["field1", "field2"],
            reader,
            "pid",
            "model",
            include_nulls=True,
        )
        holder = result["pid"]["model"]
        assert len(holder) == 2
        assert holder[0] == {"name": "field1", "value": None}
        assert holder[1] == {"name": "field2", "value": "has_value"}

    def test_deeply_wrapped_values_unwrapped(self) -> None:
        task_data = {"field": {"value": {"value": "deeply nested actual value"}}}
        reader = _make_reader({})
        result = _pipeline(task_data, "field", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert holder[0]["value"] == "deeply nested actual value"

    def test_dict_without_value_key_passed_through(self) -> None:
        task_data = {"config": {"setting": True, "enabled": False}}
        reader = _make_reader({})
        result = _pipeline(task_data, "config", reader, "pid", "model")

        holder = result["pid"]["model"]
        assert holder[0]["value"] == {"setting": True, "enabled": False}

    def test_reader_returning_non_list_resets_holder(self) -> None:
        """If the KKV store returns a non-list (corrupt data), holder resets to []."""

        def bad_reader(k1: str, k2: str) -> str:
            return "not a list"

        result = _pipeline({"field": "value"}, "field", bad_reader, "pid", "model")
        assert result["pid"]["model"] == [{"name": "field", "value": "value"}]

    def test_large_vars_array_performance(self) -> None:
        """Ensure no quadratic behavior with many fields."""
        n = 500
        variable_names = [f"field_{i}" for i in range(n)]
        task_data = {name: f"value_{i}" for i, name in enumerate(variable_names)}
        reader = _make_reader({})
        result = _pipeline(task_data, variable_names, reader, "pid", "model")

        holder = result["pid"]["model"]
        assert len(holder) == n
        assert holder[0] == {"name": "field_0", "value": "value_0"}
        assert holder[-1] == {"name": f"field_{n - 1}", "value": f"value_{n - 1}"}
