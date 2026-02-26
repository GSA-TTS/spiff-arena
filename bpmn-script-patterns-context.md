# BPMN Pre/PostScript Pattern Analysis — Context Transfer

> Generated from analysis of 31 BPMN files under `workflow/process_models/PIC/`
> Date: February 25, 2026

---

## Project Overview

This is a GSA-TTS project (PIC BLM CxWorks) providing workflow automation for NEPA permitting processes. The system uses **SpiffWorkflow** as its BPMN engine with an **Astro SSR frontend**. Process models are stored as `.bpmn` XML files in `workflow/process_models/`.

Python scripts are embedded directly in the BPMN XML inside `<spiffworkflow:preScript>` (runs before a task executes) and `<spiffworkflow:postScript>` (runs after a task completes). These scripts manipulate workflow variables that persist across tasks.

---

## File Inventory (31 BPMN files)

### Agency CE Workflows (main workflows — heaviest script usage)

- `agency-specific-processes/baseline-ce/baseline-ce.bpmn`
- `agency-specific-processes/blm-ce-generic/blm-ce-generic.bpmn`
- `agency-specific-processes/blm-ce-moab copy/blm-ce-moab-reborn.bpmn`
- `agency-specific-processes/doe-ce/doe-ce.bpmn`
- `agency-specific-processes/epa-ce/epa-ce.bpmn`
- `agency-specific-processes/fra-ce/fra-ce.bpmn`
- `agency-specific-processes/short-ce/short-ce.bpmn`
- `agency-specific-processes/dhs/dhs.bpmn`

### Utility Subprocesses

- `agency-specific-processes/id-team-subprocess/id-team-subprocess.bpmn`
- `agency-specific-processes/ce-initialization/ce-initialization.bpmn`
- `agency-specific-processes/make-pdf/make-pdf.bpmn`
- `agency-specific-processes/manual-form-standalone/manual-form-standalone.bpmn`
- `agency-specific-processes/nepa-assist-api-call/nepa-assist-api-call.bpmn`
- `agency-specific-processes/ID-team-only/id-team-only.bpmn`
- `agency-specific-processes/manage-id-team-checklist/manage-id-team-checklist.bpmn`
- `agency-specific-processes/copy-blm-moab-ce/copy-blm-moab-ce.bpmn`
- `agency-specific-processes/upsert-single-data-element/upsert-single-data-element.bpmn`

### AI/API Integration

- `agency-specific-processes/ai-search-subprocess/ai-search-subprocess.bpmn`
- `agency-specific-processes/ai-improve-pd-process/ai-improve-pd-process.bpmn`

### Files with No Scripts (pure BPMN structure)

- `agency-specific-processes/data-populator/data-populator.bpmn`
- `agency-specific-processes/parallel-review/parallel-review.bpmn`
- `agency-specific-processes/copy-payload/copy-payload.bpmn`
- `agency-specific-processes/general-form-2/general-form-2.bpmn`
- `agency-specific-processes/populate-management-objects/populate-management-objects.bpmn`
- `agency-specific-processes/write-decision-payloads-to-persistent-storage/write-decision-payloads-to-persistent-storage.bpmn`
- `agency-specific-processes/write-management-to-persistent-storage/write-management-to-persistent-storage.bpmn`
- `agency-specific-processes/initialization-process/initialization-process.bpmn`
- `reusable-processes/hello-ce/doc-ce-a-1.bpmn`
- `reusable-processes/hello-ce-2/hello-ce-2.bpmn`
- `reusable-processes/parallel-review-outer/parallel-review-outer.bpmn`
- `examples/helpers-test/helpers-test.bpmn`

---

## Copy-Paste Inheritance Tiers

The scripts reveal clear **family groupings** based on code duplication:

1. **BLM-Moab full** (blm-ce-generic, blm-ce-moab-reborn, baseline-ce) — most complex, with ID team, LUP helpers, preview HTML, multiple PDF generation stages
2. **Simple agency** (doe-ce, epa-ce, fra-ce, short-ce) — shared structure, simpler field maps, no LUP/preview features
3. **DHS** — similar to simple family but with different step names and extra approval stages (OGC, Project Proponent)
4. **Utility subprocesses** (id-team-subprocess, ce-initialization, make-pdf) — single-purpose focused scripts
5. **AI/API** (ai-search-subprocess, nepa-assist-api-call) — external integration scripts

---

## Pattern 1: Status Bar Tracking

**Location:** Always `preScript`
**Purpose:** Controls the visual progress/step indicator in the Astro frontend.

```python
status_bar_step = 'ce-helper'
status_bar_role = 'aa'
```

### `status_bar_step` Values

| Value                                         | Meaning                                    |
| --------------------------------------------- | ------------------------------------------ |
| `'ce-helper'`                                 | CE selection helper page                   |
| `'ce-form'`                                   | CE documentation form                      |
| `'conditions-helper'`                         | Conditions/LUP helper page                 |
| `'conditions-form'`                           | Conditions entry form                      |
| `'ce-determination-review'`                   | Final CE review stage                      |
| `'complete'`                                  | Process is done                            |
| `'resource-use-checklist-step1'`              | ID team resource checklist (analyst entry) |
| `'resource-use-checklist-step2'`              | Geospatial/NEPAssist step                  |
| `'resource-use-checklist-step3'`              | ID team checklist UI                       |
| `'address-extraordinary-circumstances-step1'` | EC helper                                  |
| `'address-extraordinary-circumstances-step2'` | EC form                                    |
| `'other-obligations-helper'`                  | Other obligations helper                   |
| `'other-obligations-form'`                    | Other obligations form                     |
| `'project-info-review'`                       | Supervisor review stage                    |
| `'project-information-form'`                  | Project data entry (DHS)                   |
| `'ec-helper'`                                 | EC helper (DHS variant)                    |
| `'ec-form'`                                   | EC form (DHS variant)                      |
| `'complete-review'`                           | DHS review stage                           |
| `'evaluation'`                                | DHS evaluation step                        |
| `'enter-project-info'`                        | CE initialization entry                    |

### `status_bar_role` Values

| Value  | Meaning                              |
| ------ | ------------------------------------ |
| `'aa'` | "Action Agent" / analyst lane        |
| `'rr'` | "Reviewer/Responsible Official" lane |

**Found in:** Every agency CE file (baseline-ce, blm-ce-generic, blm-ce-moab-reborn, doe-ce, epa-ce, fra-ce, short-ce, dhs, nepa-assist-api-call)

---

## Pattern 2: `alt_task_title` — Dual Purpose

### In preScript — Sets visible task name

```python
alt_task_title = 'Project Data Entry'
alt_task_title = 'Document CE'
alt_task_title = 'Final Reviewer Approval'
alt_task_title = f"Complete ID Checklist Item {user}"  # dynamic
alt_task_title = f"Confirm Survey Completed for {user}"  # dynamic
```

Full list of observed values:

- `'Project Data Entry'`
- `'Document CE'`
- `'Evaluate Conditions'` / `'Conditions'`
- `'Evaluate Extraordinary Circumstances'`
- `'Other Obligations'` / `'Document Other Applicable Requirements'`
- `'Final Reviewer Approval'`
- `'Authorizing Official Approval'` / `'Authorizing Offical Approval'` (note: typo in original)
- `'Supervisor Approval - Project Information'`
- `'Approve Final CE Determination - Authorizing Official'`
- `'Edit Final CE Determination'`
- `'Enter Project Information'`
- `'Compliance with NEPA'` / `'Conformance with Land Use Plan'`

### In postScript — The `'Ignore'` Convention

```python
alt_task_title = 'Ignore'
```

**This is the single most common postScript pattern.** After a user task completes, setting `alt_task_title = 'Ignore'` signals the frontend to skip showing this task in the task list / status display. Prevents completed form tasks from cluttering the user's view.

Sometimes combined with other cleanup:

```python
alt_task_title = 'Ignore'
lane_owners["supervisor"] = assigned_reviewers
button_title = ""
```

**Found in:** Every agency CE file.

---

## Pattern 3: Process Initialization via `get_toplevel_process_info()`

**Location:** `preScript` (at workflow start)
**Purpose:** Bootstraps the process identity and configuration.

```python
process_invo = get_toplevel_process_info()

process_instance_id = str(process_invo.get("process_instance_id", ""))
process_model_identifier = process_invo.get("process_model_identifier", "")

process_id = process_instance_id
current_de_process_model = "BLM-MOAB-CE"  # agency-specific constant
lead_agency = "DOI/BLM"
process_type = "CE"
lane_owners = {}
key_values = [current_de_process_model, process_id]
```

### Agency Constants

| File                                              | `current_de_process_model` |
| ------------------------------------------------- | -------------------------- |
| baseline-ce, short-ce, fra-ce, blm-ce-moab-reborn | `"BLM-MOAB-CE"`            |
| blm-ce-generic                                    | `"BLM-CE-GENERIC"`         |
| doe-ce                                            | `"DOE-CE"`                 |
| epa-ce                                            | `"EPA-CE"`                 |
| dhs                                               | `"DHS-CE"`                 |

After initialization, files define `PROJECT_FIELD_MAP`, `PROCESS_INSTANCE_FIELD_MAP`, `project_base`, and `process_instance_base` dictionaries mapping local form fields to canonical data model fields.

**Found in:** baseline-ce, blm-ce-generic, blm-ce-moab-reborn, copy-blm-moab-ce, dhs, doe-ce, epa-ce, fra-ce, short-ce, ID-team-only

---

## Pattern 4: `decision_payloads` — Reader/Writer Data Object

A SpiffWorkflow data object used as both a callable (reader) and a dict (writer).

### As Reader (preScript):

```python
vars_array = decision_payloads(process_id, current_de_process_model)
```

### As Writer (postScript):

```python
# Keep a handle to the reader before we overwrite the name with a dict on write
_reader_decision_payloads = decision_payloads

# 1) Read the current bucket
holder = _reader_decision_payloads(process_id, current_de_process_model)
if holder is None or not isinstance(holder, list):
    holder = []

nepa_data = get_task_data_value('nepareport', None)
if nepa_data is not None:
    holder.append({"name": 'nepareport', "value": nepa_data})

# Write back
decision_payloads = { process_id: { current_de_process_model: holder } }
```

The `_reader_decision_payloads` trick preserves the callable reference before reassigning the name to a dict for the write operation.

**Reader files:** doe-ce, epa-ce, fra-ce, short-ce, baseline-ce, blm-ce-generic, blm-ce-moab-reborn
**Writer files:** doe-ce, epa-ce, fra-ce, short-ce, baseline-ce, dhs, blm-ce-moab-reborn, ce-initialization

---

## Pattern 5: `try/except` Counter Initialization

**Location:** `preScript`
**Purpose:** Tracks how many times a task has been entered (for re-entry after edits).

```python
try:
    projenter_counter += 1
except NameError:
    projenter_counter = 1
```

Variant names: `ceenter_counter`, `condenter_counter`, `ecenter_counter`, `oblenter_counter`, `iditem_counter`

On first entry, `commentshow` is typically set to `False`; on re-entry it's `True` (showing prior comments).

**Found in:** Every agency CE file.

---

## Pattern 6: Massive Variable Cleanup (`del` blocks)

**Location:** `postScript` (after extraordinary circumstances helper)
**Purpose:** Prevents intermediate form variables from polluting downstream task scopes.

```python
alt_task_title = 'Ignore'

# Clean up dropdown structure
try: del dropdown_headers
except: pass
try: del rows
except: pass

# Clean up intermediate parts and cells
try: del _ph_parts
except: pass
try: del _nr_parts
except: pass
# ... ~16 more _*_parts and _*_cell variables ...

# Clean up oX_... form field variables
try: del o1_publicsafety
except: pass
try: del o2a_historic
except: pass
# ... ~20 more o*_ variables ...

# Clean up specialist groups
try: del specialist_groups
except: pass
```

**Found identically in:** All agency CE files (baseline-ce, blm-ce-generic, blm-ce-moab-reborn, dhs, doe-ce, epa-ce, fra-ce, short-ce)

---

## Pattern 7: `specialist_groups` Construction

**Location:** `postScript`
**Purpose:** Defines the BLM interdisciplinary team structure.

```python
specialist_groups = [
    {
        "group_name": "Rangeland Specialist",
        "user_group": [username],
        "specialists": {
            "Livestock_Grazing": "Livestock Grazing",
            "Rangeland_Health_Standards": "Rangeland Health Standards"
        }
    },
    {
        "group_name": "Archeologist",
        "user_group": [username],
        "specialists": {
            "Cultural_Resources": "Cultural Resources"
        }
    },
    # ... 9 more groups covering:
    # Outdoor Recreation Planner (8 areas), Aquatic Ecologist (4),
    # Geologist (3), Natural Resource Specialist (5),
    # Wildlife Biologist (4), Fire Management (2),
    # Paleontology (1), Lands and Realty (1),
    # Air Quality/Oil & Gas (2)
]
```

Feeds into `build_id_team_schema_and_resource_list()` to generate a JSON Schema for the ID team assignment form.

**Found in:** short-ce, baseline-ce, blm-ce-moab-reborn (identical); blm-ce-generic (via CallActivity to initialization)

---

## Pattern 8: `context` Dict for Reusable Form Subprocess

**Location:** `preScript`
**Purpose:** Builds configuration for the `General_form_BLM` CallActivity subprocess.

```python
context = {
    "reviewer": lane_owners["analyst"],
    "commentshow": True,
    "moveoncheck": False,
    "process_id": process_id,
    "current_de": "1",
    "current_de_process_model": current_de_process_model,
    "instructions": "...",
    "button_instructions": "..."
}
```

Key fields:

- `reviewer` — list of usernames who can act on this task
- `commentshow` — whether to show comment bubbles (toggled by counter pattern)
- `moveoncheck` — `False` for data entry, `True` for review/approval
- `process_id` / `current_de` / `current_de_process_model` — identifies which data to load/save
- `instructions` / `button_instructions` — dynamic instruction text
- `approval_stage` — label for review stages (only when `moveoncheck=True`)
- `reviewer_options` — list of potential reviewers for assignment dropdown

**Found in:** Every agency CE file.

---

## Pattern 9: `vars_array` Construction

**Location:** Mostly `preScript`
**Purpose:** Builds `{"name": ..., "value": ...}` dicts for upserting to persistent data store.

### From `decision_payloads` reader:

```python
vars_array = decision_payloads(process_id, current_de_process_model)
```

### Manual construction:

```python
vars_array = []
value = get_task_data_value("exclusionsText", None)
vars_array.append({"name": "exclusionsText", "value": value})

upsert_context = {
    "data": vars_array,
    "key": key_values
}
```

### Forced variable list pattern:

```python
forced_vars = [
    "publicHealthImpacts",
    "naturalResourcesImpacts",
    "controversialEffects",
    "precedentForFutureAction",
    "cumulativeImpacts",
    "endangeredSpeciesImpacts",
    "limitAccessToSacredSites",
    "promoteNoxiousWeeds",
    "categoricalExclusionJustification",
]

vars_array = []
for name in forced_vars:
    value = get_task_data_value(name, None)
    vars_array.append({"name": name, "value": value})

upsert_context = {
    "data": vars_array,
    "key": key_values
}
```

### ID team checklist variant:

```python
vars_array = []
value_obj = {}
for field in ["impact", "rationale", "specialist", "date"]:
    v = get_task_data_value(field, None)
    if v is not None:
        value_obj[field] = v

if value_obj:
    vars_array.append({
        "name": var_name,
        "value": value_obj
    })

upsert_context = {
    "data": vars_array,
    "key": key_values
}
```

---

## Pattern 10: `button_title` UI Customization

**Location:** `preScript`

```python
button_title = '<buttonlabel button-label="Submit">'
```

Or BLM variant:

```python
button_title = '<button-label button-label="Submit"></button-label>'
```

Cleaned up in postScript: `button_title = ""`

**Found in:** doe-ce, epa-ce, fra-ce, short-ce, baseline-ce, blm-ce-generic, blm-ce-moab-reborn

---

## Pattern 11: User Handling

### `get_process_initiator_user()` (ce-initialization, copy-blm-moab-ce, ID-team-only):

```python
if not username:
    current_user = get_process_initiator_user() or {}
    if isinstance(current_user, dict):
        username = current_user.get("username")
    else:
        username = current_user
```

### `username` in `skipID` flow (baseline-ce, blm-ce-generic, blm-ce-moab-reborn, ID-team-only):

```python
if skipID == "Yes":
    if username:
        admin_members = get_group_members("admin") or []
        for group in specialist_groups:
            base = list(admin_members)
            if username not in base:
                base.append(username)
            group["user_group"] = base
```

---

## Pattern 12: `lane_owners` Management

Initialized after `get_toplevel_process_info()`, populated via `get_group_members()`:

```python
lane_owners["approver"] = get_group_members("admin") + get_group_members("blm-moab-ao")
lane_owners["specialist"] = get_group_members("admin")
lane_owners["reviewer"] = get_group_members("admin") + get_group_members("blm-moab-nepa-coord")
lane_owners["supervisor"] = get_group_members("admin") + get_group_members("blm-moab-supervisors")
original_supervisors = get_group_members("admin") + get_group_members("blm-moab-supervisors")
```

Dynamically updated during workflow: `lane_owners["supervisor"] = assigned_reviewers`

---

## Pattern 13: `form_data` Extraction for PDF

**Location:** `preScript`

```python
task_data = get_current_task_data()
form_data = {}
attachments = []

for k, v in task_data.items():
    if k == "approvers":
        form_data[k] = v
        continue
    if k == "allIdTeamChecklistResources":
        form_data[k] = v
        continue
    if k == "idTeamChecklist":
        form_data[k] = v
        continue
    if k == "attachments":
        for attachment in v["value"]:
            attachments.append(get_encoded_file_data(attachment))
        form_data[k] = attachments
    if not isinstance(v, (str, int, dict)):
        continue
    if isinstance(v, str) or isinstance(v, int):
        form_data[k] = v
    elif "value" in v:
        if isinstance(v["value"], str):
            form_data[k] = v["value"]

del task_data
del attachments
```

**Found in:** blm-ce-generic (×3), blm-ce-moab-reborn (×3), make-pdf

---

## Pattern 14: CE Exclusion Text Aggregation

### BLM variant (baseline-ce, blm-ce-generic, blm-ce-moab-reborn, short-ce):

```python
matches = [v for k, v in item.items() if k.startswith("exclusion_")]
val = matches[0] if matches else {}
```

### Other agency variant (doe-ce, epa-ce, fra-ce, dhs):

```python
excl = item.get("exclusion") or {}
val = excl.get("value")
```

---

## Pattern 15: `previewHtml` iframe Embedding

**Location:** `preScript` (blm-ce-generic, blm-ce-moab-reborn only)

```python
previewHtml = previewDataResponse["body"]["previewData"]
previewHtml = f'<iframe src="data:text/html;base64,{previewHtml}" style="width:100%; min-height:1000px;"></iframe>'
```

Embeds a base64-encoded HTML preview of the CE determination document for review tasks.

---

## BPMN-Level Patterns (Beyond Scripts)

### Namespace

```xml
xmlns:spiffworkflow="http://spiffworkflow.org/bpmn/schema/1.0/core"
```

### Service Task Operators

- `artifacts/GenerateArtifact` — PDF generation
- `artifacts/GenerateHtmlPreview` — HTML preview generation
- `http/GetRequest` — HTTP GET calls

### CallActivity Targets

- `General_form_BLM` — generic form rendering subprocess (used by all steps)
- `Process_ce_initialization_kdfs` — initialization subprocess
- `Process_write_decision_payloads_to_persistent_storage_d0sxc1h` — data persistence
- `Process_nepa_assist_api_call_ybuhhlr` — geospatial screening
- `Process_id_team_subprocess_yg2of13` — ID team checklist processing

### `spiffworkflow:instructionsForEndUser`

Rich Jinja2 templates including:

- `{{ previewHtml | safe }}` — rendered HTML previews
- `{{ pdfData.body.presigned_link }}` — download links
- `{% for item in vars_array %}` — data loops
- `<button-label>` custom components

---

## SpiffWorkflow Built-in Functions Referenced

| Function                            | Purpose                                     |
| ----------------------------------- | ------------------------------------------- |
| `get_toplevel_process_info()`       | Returns process instance metadata           |
| `get_process_initiator_user()`      | Returns the user who started the process    |
| `process_current_user()`            | Returns the currently active user           |
| `get_group_members(group_name)`     | Returns list of users in a workflow group   |
| `get_current_task_data()`           | Returns all data from the current task      |
| `get_task_data_value(key, default)` | Gets a specific value from task data        |
| `get_encoded_file_data(attachment)` | Returns base64-encoded file data            |
| `decision_payloads(pid, model)`     | Reads from the decision payloads data store |

---

## Key Observations for Script Task Refactoring

1. **High duplication** — The initialization block, EC cleanup block, and specialist_groups definition are copy-pasted verbatim across 5-8 files each.
2. **The `'Ignore'` postScript pattern** is so ubiquitous it could be a framework-level feature rather than inline code.
3. **Counter + commentshow** is a universal pattern that could be abstracted.
4. **`decision_payloads` reader/writer** requires the `_reader_decision_payloads` workaround due to SpiffWorkflow's data object mechanics — any refactoring needs to preserve this.
5. **`context` dict construction** follows a consistent schema but with agency-specific variations in field maps and instructions.
6. **Status bar values** are string-based with no central enum — a shared constants definition would reduce typo risk.
