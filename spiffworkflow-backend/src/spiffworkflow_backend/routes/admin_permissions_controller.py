from typing import Any

import flask.wrappers
from flask import jsonify
from flask import make_response

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.group import GroupModel
from spiffworkflow_backend.models.permission_assignment import PermissionAssignmentModel
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.process_model_service import ProcessModelService


def admin_group_permissions_list(group_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    if group.principal is None:
        return make_response(jsonify({"results": []}), 200)

    assignments = (
        PermissionAssignmentModel.query.filter_by(principal_id=group.principal.id)
        .order_by(PermissionAssignmentModel.id)
        .all()
    )

    results = [
        {
            "id": a.id,
            "permission": a.permission,
            "grant_type": a.grant_type,
            "target_uri": a.permission_target.uri if a.permission_target else None,
        }
        for a in assignments
    ]
    return make_response(jsonify({"results": results}), 200)


def admin_group_permissions_create(group_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    if group.principal is None:
        raise ApiError(
            error_code="admin_group_no_principal",
            message=f"Group {group_id} has no principal. It may not have been created properly.",
            status_code=400,
        )

    permission = body.get("permission")
    target_uri = body.get("target_uri")
    grant_type = body.get("grant_type", "permit")

    if not permission or not target_uri:
        raise ApiError(
            error_code="admin_permission_fields_required",
            message="Both 'permission' and 'target_uri' are required.",
            status_code=400,
        )

    permission_target = AuthorizationService.find_or_create_permission_target(target_uri)
    assignment = AuthorizationService.create_permission_for_principal(
        group.principal, permission_target, permission, grant_type
    )

    result = {
        "id": assignment.id,
        "permission": assignment.permission,
        "grant_type": assignment.grant_type,
        "target_uri": assignment.permission_target.uri if assignment.permission_target else None,
    }
    return make_response(jsonify(result), 201)


def admin_group_permissions_delete(group_id: int, permission_id: int) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    assignment = db.session.get(PermissionAssignmentModel, permission_id)
    if assignment is None:
        raise ApiError(
            error_code="admin_permission_not_found",
            message=f"Permission assignment {permission_id} not found.",
            status_code=404,
        )

    if group.principal is None or assignment.principal_id != group.principal.id:
        raise ApiError(
            error_code="admin_permission_wrong_group",
            message=f"Permission assignment {permission_id} does not belong to group {group_id}.",
            status_code=400,
        )

    db.session.delete(assignment)
    db.session.commit()
    return make_response(jsonify({"ok": True}), 200)


def admin_group_apply_role_preset(group_id: int, body: dict[str, Any]) -> flask.wrappers.Response:
    group = db.session.get(GroupModel, group_id)
    if group is None:
        raise ApiError(
            error_code="admin_group_not_found",
            message=f"Group {group_id} not found.",
            status_code=404,
        )

    if group.principal is None:
        raise ApiError(
            error_code="admin_group_no_principal",
            message=f"Group {group_id} has no principal.",
            status_code=400,
        )

    process_group_identifier = body.get("process_group_identifier")
    role = body.get("role", "user")

    if not process_group_identifier:
        raise ApiError(
            error_code="admin_process_group_required",
            message="'process_group_identifier' is required.",
            status_code=400,
        )

    if role == "admin":
        permissions_to_assign = AuthorizationService.set_elevated_permissions()
        pg_permissions = AuthorizationService.set_process_group_permissions(
            f"PG:{process_group_identifier}", "all"
        )
    else:
        permissions_to_assign = AuthorizationService.set_basic_permissions()
        pg_permissions = AuthorizationService.set_process_group_permissions(
            f"PG:{process_group_identifier}", "start"
        )

    all_permissions = permissions_to_assign + pg_permissions
    created_count = 0
    for pta in all_permissions:
        permission_target = AuthorizationService.find_or_create_permission_target(pta.target_uri)
        AuthorizationService.create_permission_for_principal(
            group.principal, permission_target, pta.permission
        )
        created_count += 1

    return make_response(jsonify({"ok": True, "permissions_applied": created_count}), 200)


def admin_process_group_list() -> flask.wrappers.Response:
    process_groups = ProcessModelService.get_process_groups_for_api()
    results = [
        {
            "id": pg.id,
            "display_name": pg.display_name,
        }
        for pg in process_groups
    ]
    return make_response(jsonify({"results": results}), 200)
