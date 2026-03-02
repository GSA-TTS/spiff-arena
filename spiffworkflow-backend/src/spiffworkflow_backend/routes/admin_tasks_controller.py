from typing import Any

import flask.wrappers
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.human_task import HumanTaskModel
from spiffworkflow_backend.models.human_task_user import HumanTaskUserAddedBy
from spiffworkflow_backend.models.human_task_user import HumanTaskUserModel
from spiffworkflow_backend.models.process_instance import ProcessInstanceModel
from spiffworkflow_backend.models.user import UserModel


def _human_task_to_dict(ht: HumanTaskModel) -> dict[str, Any]:
    potential_owners = [
        {"id": u.id, "username": u.username}
        for u in ht.potential_owners
    ]
    completed_by = None
    if ht.completed_by_user:
        completed_by = {"id": ht.completed_by_user.id, "username": ht.completed_by_user.username}

    lane_group = None
    if ht.lane_assignment_id:
        group = db.session.get(GroupModel, ht.lane_assignment_id)
        if group:
            lane_group = {"id": group.id, "identifier": group.identifier}

    return {
        "id": ht.id,
        "task_guid": ht.task_guid,
        "task_name": ht.task_name,
        "task_title": ht.task_title,
        "task_type": ht.task_type,
        "task_status": ht.task_status,
        "completed": ht.completed,
        "lane_name": ht.lane_name,
        "lane_group": lane_group,
        "potential_owners": potential_owners,
        "completed_by": completed_by,
    }


def admin_pi_tasks(pid: int) -> flask.wrappers.Response:
    process_instance = db.session.get(ProcessInstanceModel, pid)
    if process_instance is None:
        raise ApiError(
            error_code="admin_process_instance_not_found",
            message=f"Process instance {pid} not found.",
            status_code=404,
        )

    human_tasks = (
        HumanTaskModel.query.filter_by(process_instance_id=pid)
        .order_by(HumanTaskModel.id)
        .all()
    )

    results = [_human_task_to_dict(ht) for ht in human_tasks]
    return make_response(jsonify({
        "process_instance": {
            "id": process_instance.id,
            "status": process_instance.status,
            "process_model_identifier": process_instance.process_model_identifier,
            "process_model_display_name": process_instance.process_model_display_name,
        },
        "results": results,
    }), 200)


def admin_task_reassign(human_task_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    human_task = db.session.get(HumanTaskModel, human_task_id)
    if human_task is None:
        raise ApiError(
            error_code="admin_human_task_not_found",
            message=f"Human task {human_task_id} not found.",
            status_code=404,
        )

    user_ids: list[int] = body.get("user_ids", [])
    if not user_ids:
        raise ApiError(
            error_code="admin_no_user_ids",
            message="At least one user_id is required.",
            status_code=400,
        )

    # Remove existing manual/lane_assignment owners
    HumanTaskUserModel.query.filter_by(human_task_id=human_task.id).delete()
    db.session.flush()

    for uid in user_ids:
        user = db.session.get(UserModel, uid)
        if user is None:
            raise ApiError(
                error_code="admin_user_not_found",
                message=f"User {uid} not found.",
                status_code=404,
            )
        htu = HumanTaskUserModel(
            human_task_id=human_task.id,
            user_id=uid,
            added_by=HumanTaskUserAddedBy.manual.value,
        )
        db.session.add(htu)

    db.session.commit()
    return make_response(jsonify(_human_task_to_dict(human_task)), 200)


def admin_task_add_owners(human_task_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    human_task = db.session.get(HumanTaskModel, human_task_id)
    if human_task is None:
        raise ApiError(
            error_code="admin_human_task_not_found",
            message=f"Human task {human_task_id} not found.",
            status_code=404,
        )

    user_ids: list[int] = body.get("user_ids", [])
    if not user_ids:
        raise ApiError(
            error_code="admin_no_user_ids",
            message="At least one user_id is required.",
            status_code=400,
        )

    for uid in user_ids:
        user = db.session.get(UserModel, uid)
        if user is None:
            raise ApiError(
                error_code="admin_user_not_found",
                message=f"User {uid} not found.",
                status_code=404,
            )
        existing = HumanTaskUserModel.query.filter_by(human_task_id=human_task.id, user_id=uid).first()
        if existing is None:
            htu = HumanTaskUserModel(
                human_task_id=human_task.id,
                user_id=uid,
                added_by=HumanTaskUserAddedBy.manual.value,
            )
            db.session.add(htu)

    db.session.commit()
    return make_response(jsonify(_human_task_to_dict(human_task)), 200)


def admin_task_lane_reassign(human_task_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    human_task = db.session.get(HumanTaskModel, human_task_id)
    if human_task is None:
        raise ApiError(
            error_code="admin_human_task_not_found",
            message=f"Human task {human_task_id} not found.",
            status_code=404,
        )

    group_id: int | None = body.get("group_id")
    if group_id is None:
        raise ApiError(
            error_code="admin_group_id_required",
            message="'group_id' is required.",
            status_code=400,
        )

    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    human_task.lane_assignment_id = group.id

    # Recalculate potential owners from new group members
    HumanTaskUserModel.query.filter_by(
        human_task_id=human_task.id,
        added_by=HumanTaskUserAddedBy.lane_assignment.value,
    ).delete()
    db.session.flush()

    for user in group.users:
        existing = HumanTaskUserModel.query.filter_by(human_task_id=human_task.id, user_id=user.id).first()
        if existing is None:
            htu = HumanTaskUserModel(
                human_task_id=human_task.id,
                user_id=user.id,
                added_by=HumanTaskUserAddedBy.lane_assignment.value,
            )
            db.session.add(htu)

    db.session.add(human_task)
    db.session.commit()
    return make_response(jsonify(_human_task_to_dict(human_task)), 200)


def admin_lane_reassign_bulk(pid: int, body: dict[str, Any]) -> flask.wrappers.Response:
    process_instance = db.session.get(ProcessInstanceModel, pid)
    if process_instance is None:
        raise ApiError(
            error_code="admin_process_instance_not_found",
            message=f"Process instance {pid} not found.",
            status_code=404,
        )

    lane_name: str | None = body.get("lane_name")
    group_id: int | None = body.get("group_id")

    if lane_name is None or group_id is None:
        raise ApiError(
            error_code="admin_lane_and_group_required",
            message="Both 'lane_name' and 'group_id' are required.",
            status_code=400,
        )

    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    human_tasks = HumanTaskModel.query.filter_by(
        process_instance_id=pid,
        lane_name=lane_name,
        completed=False,
    ).all()

    updated_count = 0
    for ht in human_tasks:
        ht.lane_assignment_id = group.id

        HumanTaskUserModel.query.filter_by(
            human_task_id=ht.id,
            added_by=HumanTaskUserAddedBy.lane_assignment.value,
        ).delete()

        for user in group.users:
            existing = HumanTaskUserModel.query.filter_by(human_task_id=ht.id, user_id=user.id).first()
            if existing is None:
                htu = HumanTaskUserModel(
                    human_task_id=ht.id,
                    user_id=user.id,
                    added_by=HumanTaskUserAddedBy.lane_assignment.value,
                )
                db.session.add(htu)

        db.session.add(ht)
        updated_count += 1

    db.session.commit()
    return make_response(jsonify({"ok": True, "tasks_updated": updated_count}), 200)
