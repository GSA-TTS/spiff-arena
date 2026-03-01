from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import ForeignKey

from spiffworkflow_backend.models.db import SpiffworkflowBaseDBModel
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.json_data import JsonDataModel  # noqa: F401
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel


@dataclass
class TaskNavigationSnapshotModel(SpiffworkflowBaseDBModel):
    __tablename__ = "task_navigation_snapshot"

    id: int = db.Column(db.Integer, primary_key=True)
    process_instance_id: int = db.Column(ForeignKey(ProcessInstanceModel.id), nullable=False, index=True)  # type: ignore

    # a colon delimited path of bpmn_process_definition_ids for a given task (same as TaskDraftDataModel)
    task_definition_id_path: str = db.Column(db.String(255), nullable=False, index=True)

    json_data_hash: str = db.Column(db.String(255), nullable=False, index=True)

    # ordering in the human task chain
    navigation_sequence: int = db.Column(db.Integer, nullable=False)

    # original task guid
    task_guid: str = db.Column(db.String(50), nullable=False)

    # bpmn name for display
    bpmn_identifier: str = db.Column(db.String(255), nullable=False)

    def get_snapshot_data(self) -> dict | None:
        return JsonDataModel.find_data_dict_by_hash(self.json_data_hash)
