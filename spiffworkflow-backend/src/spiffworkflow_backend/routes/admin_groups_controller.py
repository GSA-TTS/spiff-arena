import csv
import io
from typing import Any

import flask.wrappers
from flask import jsonify
from flask import make_response
from flask import request

from sqlalchemy import or_

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.user import UserModel
from spiffworkflow_backend.models.user_group_assignment import UserGroupAssignmentModel
from spiffworkflow_backend.models.user_group_assignment_waiting import UserGroupAssignmentWaitingModel
from spiffworkflow_backend.services.user_service import UserService


def _group_to_dict(group: GroupModel) -> dict[str, Any]:
    member_count = UserGroupAssignmentModel.query.filter_by(group_id=group.id).count()
    pending_count = UserGroupAssignmentWaitingModel.query.filter_by(group_id=group.id).count()
    return {
        "id": group.id,
        "identifier": group.identifier,
        "name": group.name or group.identifier,
        "source_is_open_id": group.source_is_open_id,
        "member_count": member_count,
        "pending_count": pending_count,
    }


def _group_detail_dict(group: GroupModel) -> dict[str, Any]:
    result = _group_to_dict(group)
    members = (
        db.session.query(UserModel, UserGroupAssignmentModel)
        .join(UserGroupAssignmentModel, UserModel.id == UserGroupAssignmentModel.user_id)
        .filter(UserGroupAssignmentModel.group_id == group.id)
        .all()
    )
    result["members"] = [
        {
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "assignment_id": assignment.id,
            "annotation": assignment.annotation,
        }
        for user, assignment in members
    ]
    pending = UserGroupAssignmentWaitingModel.query.filter_by(group_id=group.id).all()
    result["pending"] = [
        {
            "id": p.id,
            "username": p.username,
        }
        for p in pending
    ]
    return result


def admin_group_list(
    page: int = 1,
    per_page: int = 50,
) -> flask.wrappers.Response:
    groups_query = GroupModel.query.order_by(GroupModel.identifier)
    total = groups_query.count()
    groups = groups_query.offset((page - 1) * per_page).limit(per_page).all()

    pages = total // per_page
    if total % per_page > 0:
        pages += 1

    response_json = {
        "results": [_group_to_dict(g) for g in groups],
        "pagination": {
            "count": len(groups),
            "total": total,
            "pages": pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def admin_group_create(body: dict[str, Any]) -> flask.wrappers.Response:
    identifier = body.get("identifier")
    if not identifier:
        raise ApiError(
            error_code="admin_group_identifier_required",
            message="Group identifier is required.",
            status_code=400,
        )
    name = body.get("name", identifier)

    existing = GroupModel.query.filter_by(identifier=identifier).first()
    if existing:
        raise ApiError(
            error_code="admin_group_already_exists",
            message=f"Group with identifier '{identifier}' already exists.",
            status_code=400,
        )

    group = UserService.find_or_create_group(identifier)
    group.name = name
    db.session.add(group)
    db.session.commit()

    return make_response(jsonify(_group_to_dict(group)), 201)


def admin_group_show(group_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )
    return make_response(jsonify(_group_detail_dict(group)), 200)


def admin_group_update(group_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    if "name" in body:
        group.name = body["name"]
    if "identifier" in body:
        existing = GroupModel.query.filter_by(identifier=body["identifier"]).first()
        if existing and existing.id != group.id:
            raise ApiError(
                error_code="admin_group_identifier_taken",
                message=f"Group identifier '{body['identifier']}' is already in use.",
                status_code=400,
            )
        group.identifier = body["identifier"]

    db.session.add(group)
    db.session.commit()
    return make_response(jsonify(_group_to_dict(group)), 200)


def admin_group_delete(group_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )
    if group.source_is_open_id:
        raise ApiError(
            error_code="admin_cannot_delete_openid_group",
            message=f"Cannot delete OpenID-managed group '{group.identifier}'.",
            status_code=400,
        )

    db.session.delete(group)
    db.session.commit()
    return make_response(jsonify({"ok": True}), 200)


def admin_group_add_members(group_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    usernames: list[str] = body.get("usernames", [])
    if not usernames:
        raise ApiError(
            error_code="admin_no_usernames_provided",
            message="At least one username or email is required.",
            status_code=400,
        )

    added: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []

    for username_or_email in usernames:
        username_or_email = username_or_email.strip()
        if not username_or_email:
            continue
        wugam, user_to_groups = UserService.add_user_to_group_or_add_to_waiting(
            username_or_email, group.identifier
        )
        if wugam is not None:
            pending.append({"username": username_or_email, "waiting_id": wugam.id})
        else:
            for utg in user_to_groups:
                added.append({"username": utg["username"], "group_identifier": utg["group_identifier"]})

    return make_response(jsonify({"added": added, "pending": pending}), 200)


def admin_group_add_members_csv(group_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    if "file" not in request.files:
        raise ApiError(
            error_code="admin_csv_file_required",
            message="A CSV file is required.",
            status_code=400,
        )

    file = request.files["file"]
    content = file.read().decode("utf-8")
    reader = csv.reader(io.StringIO(content))

    added: list[dict[str, Any]] = []
    pending: list[dict[str, Any]] = []

    for row in reader:
        username_or_email = row[0].strip() if row else ""
        if not username_or_email:
            continue
        wugam, user_to_groups = UserService.add_user_to_group_or_add_to_waiting(
            username_or_email, group.identifier
        )
        if wugam is not None:
            pending.append({"username": username_or_email, "waiting_id": wugam.id})
        else:
            for utg in user_to_groups:
                added.append({"username": utg["username"], "group_identifier": utg["group_identifier"]})

    return make_response(jsonify({"added": added, "pending": pending}), 200)


def admin_group_remove_member(group_id: int, user_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    user = db.session.get(UserModel, user_id)
    if user is None:
        raise ApiError(
            error_code="admin_user_not_found",
            message=f"User {user_id} not found.",
            status_code=404,
        )

    UserService.remove_user_from_group(user, group.id)
    return make_response(jsonify({"ok": True}), 200)


def admin_group_remove_pending(group_id: int, waiting_id: int) -> flask.wrappers.Response:
    waiting = db.session.get(UserGroupAssignmentWaitingModel, waiting_id)
    if waiting is None or waiting.group_id != group_id:
        raise ApiError(
            error_code="admin_pending_not_found",
            message=f"Pending assignment {waiting_id} not found for group {group_id}.",
            status_code=404,
        )

    db.session.delete(waiting)
    db.session.commit()
    return make_response(jsonify({"ok": True}), 200)


def admin_group_member_annotation_update(group_id: int, user_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    assignment = UserGroupAssignmentModel.query.filter_by(user_id=user_id, group_id=group_id).first()
    if assignment is None:
        raise ApiError(
            error_code="admin_assignment_not_found",
            message=f"User {user_id} is not a member of group {group_id}.",
            status_code=404,
        )

    assignment.annotation = body.get("annotation")
    db.session.add(assignment)
    db.session.commit()
    return make_response(jsonify({"ok": True}), 200)


def admin_pending_list(
    page: int = 1,
    per_page: int = 50,
) -> flask.wrappers.Response:
    query = UserGroupAssignmentWaitingModel.query.order_by(UserGroupAssignmentWaitingModel.id)
    total = query.count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()

    pages = total // per_page
    if total % per_page > 0:
        pages += 1

    response_json = {
        "results": [
            {
                "id": item.id,
                "username": item.username,
                "group_id": item.group_id,
                "group_identifier": item.group.identifier if item.group else None,
            }
            for item in items
        ],
        "pagination": {
            "count": len(items),
            "total": total,
            "pages": pages,
        },
    }
    return make_response(jsonify(response_json), 200)


def admin_reprocess_pending(group_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    pending = UserGroupAssignmentWaitingModel.query.filter_by(group_id=group.id).all()
    resolved: list[dict[str, str]] = []

    # Collect the data we need before any DB operations that might invalidate objects
    pending_data = [
        {"id": p.id, "username": p.username, "is_wildcard": p.is_wildcard()}
        for p in pending
    ]

    for item in pending_data:
        if item["is_wildcard"]:
            continue
        user = UserModel.query.filter(
            or_(UserModel.username == item["username"], UserModel.email == item["username"])
        ).first()
        if user:
            UserService.add_user_to_group(user, group)
            assignment = UserGroupAssignmentWaitingModel.query.filter_by(id=item["id"]).first()
            if assignment is not None:
                db.session.delete(assignment)
            resolved.append({"username": item["username"], "user_id": str(user.id)})

    db.session.commit()
    return make_response(jsonify({"resolved": resolved}), 200)
