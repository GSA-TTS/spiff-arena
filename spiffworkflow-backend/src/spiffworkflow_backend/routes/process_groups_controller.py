"""APIs for dealing with process groups, process models, and process instances."""

import os
from typing import Any

import flask.wrappers
from flask import g
from flask import jsonify
from flask import make_response
from flask import request

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.exceptions.error import NotAuthorizedError
from spiffworkflow_backend.exceptions.process_entity_not_found_error import ProcessEntityNotFoundError
from spiffworkflow_backend.models.db import db
from spiffworkflow_backend.models.message_model import MessageModel
from spiffworkflow_backend.models.process_group import PROCESS_GROUP_KEYS_TO_UPDATE_FROM_API
from spiffworkflow_backend.models.process_group import ProcessGroup
from spiffworkflow_backend.routes.process_api_blueprint import _commit_and_push_to_git
from spiffworkflow_backend.routes.process_api_blueprint import _un_modify_modified_process_model_id
from spiffworkflow_backend.services.authorization_service import AuthorizationService
from spiffworkflow_backend.services.file_system_service import FileSystemService
from spiffworkflow_backend.services.message_definition_service import MessageDefinitionService
from spiffworkflow_backend.services.process_group_package_service import ProcessGroupPackageService
from spiffworkflow_backend.services.process_model_service import ProcessModelService
from spiffworkflow_backend.services.process_model_service import ProcessModelWithInstancesNotDeletableError
from spiffworkflow_backend.services.spec_file_service import SpecFileService
from spiffworkflow_backend.services.user_service import UserService


def process_group_create(body: dict) -> flask.wrappers.Response:
    process_group = ProcessGroup.from_dict(body)

    if ProcessModelService.is_process_model_identifier(process_group.id):
        raise ApiError(
            error_code="process_model_with_id_already_exists",
            message=f"Process Model with given id already exists: {process_group.id}",
            status_code=400,
        )

    if ProcessModelService.is_process_group_identifier(process_group.id):
        raise ApiError(
            error_code="process_group_with_id_already_exists",
            message=f"Process Group with given id already exists: {process_group.id}",
            status_code=400,
        )

    ProcessModelService.add_process_group(process_group)
    _commit_and_push_to_git(f"User: {g.user.username} added process group {process_group.id}")
    return make_response(jsonify(process_group), 201)


def process_group_delete(modified_process_group_id: str) -> flask.wrappers.Response:
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)

    try:
        ProcessModelService.process_group_delete(process_group_id)

        # can't do this in the ProcessModelService due to circular imports
        SpecFileService.clear_caches_for_item(process_group_id=process_group_id)
        db.session.commit()

    except ProcessModelWithInstancesNotDeletableError as exception:
        raise ApiError(
            error_code="existing_instances",
            message=str(exception),
            status_code=400,
        ) from exception

    _commit_and_push_to_git(f"User: {g.user.username} deleted process group {process_group_id}")
    return make_response(jsonify({"ok": True}), 200)


def process_group_update(modified_process_group_id: str, body: dict) -> flask.wrappers.Response:
    body_filtered = {
        include_item: body[include_item] for include_item in PROCESS_GROUP_KEYS_TO_UPDATE_FROM_API if include_item in body
    }

    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    if not ProcessModelService.is_process_group_identifier(process_group_id):
        raise ApiError(
            error_code="process_group_does_not_exist",
            message=f"Process Group with given id does not exist: {process_group_id}",
            status_code=400,
        )

    process_group = ProcessGroup.from_dict({"id": process_group_id, **body_filtered})
    ProcessModelService.update_process_group(process_group)

    all_message_models: dict[tuple[str, str], MessageModel] = {}
    MessageDefinitionService.collect_message_models(process_group, process_group_id, all_message_models)
    MessageDefinitionService.delete_message_models_at_location(process_group_id)
    db.session.commit()
    MessageDefinitionService.save_all_message_models(all_message_models)
    db.session.commit()

    _commit_and_push_to_git(f"User: {g.user.username} updated process group {process_group_id}")
    return make_response(jsonify(process_group), 200)


def process_group_list(
    process_group_identifier: str | None = None, page: int = 1, per_page: int = 100
) -> flask.wrappers.Response:
    process_groups = ProcessModelService.get_process_groups_for_api(process_group_identifier)
    batch = ProcessModelService.get_batch(items=process_groups, page=page, per_page=per_page)
    pages = len(process_groups) // per_page
    remainder = len(process_groups) % per_page
    if remainder > 0:
        pages += 1

    response_json = {
        "results": [group.serialized() for group in batch],
        "pagination": {
            "count": len(batch),
            "total": len(process_groups),
            "pages": pages,
        },
    }
    return make_response(jsonify(response_json), 200)


# this action is excluded from authorization checks, so it is important that it call:
# AuthorizationService.check_permission_for_request()
# it also allows access to the process group if the user has access to read any of the process models contained in the group
def process_group_show(
    modified_process_group_id: str,
) -> Any:
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    has_access_to_group_without_considering_subgroups_and_models = True
    try:
        AuthorizationService.check_permission_for_request()
    except NotAuthorizedError:
        has_access_to_group_without_considering_subgroups_and_models = False

    try:
        user = UserService.current_user()
        if (
            has_access_to_group_without_considering_subgroups_and_models
            or AuthorizationService.is_user_allowed_to_view_process_group_with_id(user, process_group_id)
        ):
            # do not return child models and groups here since this call does not check permissions of them
            process_group = ProcessModelService.get_process_group(process_group_id, find_direct_nested_items=False)
        else:
            raise ProcessEntityNotFoundError("viewing this process group is not authorized")
    except ProcessEntityNotFoundError as exception:
        raise (
            ApiError(
                error_code="process_group_cannot_be_found",
                message=f"Process group cannot be found: {process_group_id}",
                status_code=400,
            )
        ) from exception

    process_group.parent_groups = ProcessModelService.get_parent_group_array(process_group.id)
    return make_response(jsonify(process_group), 200)


def process_group_move(modified_process_group_identifier: str, new_location: str) -> flask.wrappers.Response:
    original_process_group_id = _un_modify_modified_process_model_id(modified_process_group_identifier)
    new_process_group = ProcessModelService.process_group_move(original_process_group_id, new_location)
    _commit_and_push_to_git(f"User: {g.user.username} moved process group {original_process_group_id} to {new_process_group.id}")
    return make_response(jsonify(new_process_group), 200)


def process_group_file_list(modified_process_group_id: str) -> flask.wrappers.Response:
    """List .py files in a process group directory."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    group_path = FileSystemService.full_path_from_id(process_group_id)
    if not os.path.isdir(group_path):
        raise ApiError(
            error_code="process_group_not_found",
            message=f"Process group directory not found: {process_group_id}",
            status_code=404,
        )

    files = []
    for item in os.scandir(group_path):
        if item.is_file() and item.name.endswith(".py"):
            with open(item.path) as f:
                content = f.read()
            files.append({"name": item.name, "file_contents": content})
    return make_response(jsonify(files), 200)


def process_group_file_show(modified_process_group_id: str, file_name: str) -> flask.wrappers.Response:
    """Get content of a .py file in a process group directory."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    group_path = FileSystemService.full_path_from_id(process_group_id)
    file_path = os.path.join(group_path, file_name)
    if not os.path.isfile(file_path):
        raise ApiError(
            error_code="file_not_found",
            message=f"File not found: {file_name} in group {process_group_id}",
            status_code=404,
        )
    with open(file_path) as f:
        content = f.read()
    return make_response(jsonify({"name": file_name, "file_contents": content}), 200)


def process_group_file_create(modified_process_group_id: str, file_name: str | None = None) -> flask.wrappers.Response:
    """Create or update a .py file in a process group directory."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    group_path = FileSystemService.full_path_from_id(process_group_id)
    if not os.path.isdir(group_path):
        raise ApiError(
            error_code="process_group_not_found",
            message=f"Process group directory not found: {process_group_id}",
            status_code=404,
        )

    request_file = request.files.get("file")
    if request_file is None:
        raise ApiError(
            error_code="no_file_provided",
            message="No file was provided in the request.",
            status_code=400,
        )

    actual_file_name = file_name or request_file.filename or "script.py"
    if not actual_file_name.endswith(".py"):
        raise ApiError(
            error_code="invalid_file_type",
            message="Only .py files are allowed in process group scripts.",
            status_code=400,
        )

    file_path = os.path.join(group_path, actual_file_name)
    content = request_file.stream.read()
    with open(file_path, "wb") as f:
        f.write(content)

    _commit_and_push_to_git(f"User: {g.user.username} saved group script {actual_file_name} in {process_group_id}")
    return make_response(jsonify({"name": actual_file_name, "file_contents": content.decode("utf-8")}), 200)


def process_group_file_update(modified_process_group_id: str, file_name: str) -> flask.wrappers.Response:
    """Update a .py file in a process group directory."""
    return process_group_file_create(modified_process_group_id, file_name=file_name)


def process_group_file_delete(modified_process_group_id: str, file_name: str) -> flask.wrappers.Response:
    """Delete a .py file from a process group directory."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    group_path = FileSystemService.full_path_from_id(process_group_id)
    file_path = os.path.join(group_path, file_name)
    if not os.path.isfile(file_path):
        raise ApiError(
            error_code="file_not_found",
            message=f"File not found: {file_name} in group {process_group_id}",
            status_code=404,
        )
    os.remove(file_path)
    _commit_and_push_to_git(f"User: {g.user.username} deleted group script {file_name} from {process_group_id}")
    return make_response(jsonify({"ok": True}), 200)


def process_group_package_list(modified_process_group_id: str) -> flask.wrappers.Response:
    """List installed packages for a process group."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    packages = ProcessGroupPackageService.list_packages(process_group_id)
    return make_response(jsonify(packages), 200)


def process_group_package_install(modified_process_group_id: str, body: dict) -> flask.wrappers.Response:
    """Install a Python package into a process group's isolated directory."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    package_name = body.get("package_name", "").strip()
    if not package_name:
        raise ApiError(
            error_code="missing_package_name",
            message="package_name is required",
            status_code=400,
        )
    result = ProcessGroupPackageService.install_package(process_group_id, package_name)
    return make_response(jsonify(result), 200)


def process_group_package_uninstall(modified_process_group_id: str, package_name: str) -> flask.wrappers.Response:
    """Uninstall a Python package from a process group's isolated directory."""
    process_group_id = _un_modify_modified_process_model_id(modified_process_group_id)
    ProcessGroupPackageService.uninstall_package(process_group_id, package_name)
    return make_response(jsonify({"ok": True}), 200)
