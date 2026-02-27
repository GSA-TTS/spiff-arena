"""Service for managing per-group Python package installations."""

import os
import re
import subprocess
from typing import Any

from flask import current_app

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.file_system_service import FileSystemService

PACKAGES_DIR_NAME = ".packages"


class ProcessGroupPackageService:
    """Manages pip --target installations scoped to a process group."""

    @classmethod
    def packages_dir_for_group(cls, process_group_id: str) -> str:
        """Return the absolute path to the .packages/ directory for a group."""
        group_path = FileSystemService.full_path_from_id(process_group_id)
        return os.path.join(group_path, PACKAGES_DIR_NAME)

    @classmethod
    def list_packages(cls, process_group_id: str) -> list[dict[str, str]]:
        """List installed packages by scanning .dist-info directories."""
        packages_dir = cls.packages_dir_for_group(process_group_id)
        packages: list[dict[str, str]] = []
        if not os.path.isdir(packages_dir):
            return packages
        for item in os.scandir(packages_dir):
            if item.is_dir() and item.name.endswith(".dist-info"):
                parts = item.name[: -len(".dist-info")].rsplit("-", 1)
                name = parts[0]
                version = parts[1] if len(parts) > 1 else "unknown"
                packages.append({"name": name, "version": version})
        packages.sort(key=lambda p: p["name"].lower())
        return packages

    @classmethod
    def install_package(cls, process_group_id: str, package_name: str) -> dict[str, Any]:
        """Install a package into the group's .packages/ directory."""
        cls._validate_package_name(package_name)
        packages_dir = cls.packages_dir_for_group(process_group_id)
        os.makedirs(packages_dir, exist_ok=True)
        cls._ensure_gitignore()

        try:
            result = subprocess.run(
                ["uv", "pip", "install", "--target", packages_dir, package_name],
                capture_output=True,
                text=True,
                timeout=120,
                check=True,
            )
            current_app.logger.info(f"Installed package '{package_name}' to {packages_dir}: {result.stdout}")
        except subprocess.CalledProcessError as e:
            raise ApiError(
                error_code="package_install_failed",
                message=f"Failed to install '{package_name}': {e.stderr}",
                status_code=400,
            ) from e
        except subprocess.TimeoutExpired as e:
            raise ApiError(
                error_code="package_install_timeout",
                message=f"Installation of '{package_name}' timed out after 120 seconds",
                status_code=408,
            ) from e

        # Find the installed package to return name+version
        packages = cls.list_packages(process_group_id)
        base_name = re.split(r"[=<>!~]", package_name)[0]
        for p in packages:
            if p["name"].lower().replace("-", "_") == base_name.lower().replace("-", "_"):
                return {"name": p["name"], "version": p["version"], "ok": True}
        return {"name": base_name, "version": "unknown", "ok": True}

    @classmethod
    def uninstall_package(cls, process_group_id: str, package_name: str) -> None:
        """Uninstall a package from the group's .packages/ directory."""
        packages_dir = cls.packages_dir_for_group(process_group_id)
        if not os.path.isdir(packages_dir):
            raise ApiError(
                error_code="package_not_found",
                message=f"No packages directory for group '{process_group_id}'",
                status_code=404,
            )
        try:
            subprocess.run(
                ["uv", "pip", "uninstall", "--target", packages_dir, package_name],
                capture_output=True,
                text=True,
                timeout=60,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise ApiError(
                error_code="package_uninstall_failed",
                message=f"Failed to uninstall '{package_name}': {e.stderr}",
                status_code=400,
            ) from e

    @classmethod
    def collect_package_dirs_for_process_model(cls, process_model_identifier: str) -> list[str]:
        """Collect .packages/ directories from all ancestor groups (outermost first).

        Returns only directories that actually exist on disk.
        """
        package_dirs: list[str] = []
        for _group_id, group_path in FileSystemService.ancestor_group_directories(process_model_identifier):
            pkg_dir = os.path.join(group_path, PACKAGES_DIR_NAME)
            if os.path.isdir(pkg_dir):
                package_dirs.append(pkg_dir)
        return package_dirs

    @classmethod
    def _validate_package_name(cls, package_name: str) -> None:
        """Basic validation to prevent command injection."""
        if not re.match(r"^[a-zA-Z0-9_][a-zA-Z0-9._-]*(([=<>!~]=?|===)[a-zA-Z0-9.*+!_-]+)?$", package_name):
            raise ApiError(
                error_code="invalid_package_name",
                message=f"Invalid package name: '{package_name}'",
                status_code=400,
            )

    @classmethod
    def _ensure_gitignore(cls) -> None:
        """Ensure .packages is in the BPMN spec root .gitignore."""
        root = FileSystemService.root_path()
        gitignore_path = os.path.join(root, ".gitignore")
        pattern = ".packages"
        if os.path.isfile(gitignore_path):
            with open(gitignore_path) as f:
                if pattern in f.read().splitlines():
                    return
        with open(gitignore_path, "a") as f:
            f.write(f"\n{pattern}\n")
