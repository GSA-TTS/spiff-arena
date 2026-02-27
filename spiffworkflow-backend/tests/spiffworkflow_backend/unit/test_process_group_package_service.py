"""Tests for ProcessGroupPackageService."""

import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from flask.app import Flask

from spiffworkflow_backend.exceptions.api_error import ApiError
from spiffworkflow_backend.services.process_group_package_service import PACKAGES_DIR_NAME
from spiffworkflow_backend.services.process_group_package_service import ProcessGroupPackageService


class TestProcessGroupPackageService:
    """Unit tests for ProcessGroupPackageService."""

    # --- packages_dir_for_group ---

    def test_packages_dir_for_group_returns_correct_path(self, app: Flask) -> None:
        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value="/specs/my-group",
        ):
            result = ProcessGroupPackageService.packages_dir_for_group("my-group")
            assert result == os.path.join("/specs/my-group", PACKAGES_DIR_NAME)

    # --- list_packages ---

    def test_list_packages_returns_empty_when_no_dir(self, app: Flask) -> None:
        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value="/nonexistent",
        ):
            result = ProcessGroupPackageService.list_packages("my-group")
            assert result == []

    def test_list_packages_scans_dist_info_dirs(self, app: Flask, tmp_path: str) -> None:
        packages_dir = os.path.join(str(tmp_path), PACKAGES_DIR_NAME)
        os.makedirs(packages_dir)
        os.makedirs(os.path.join(packages_dir, "requests-2.31.0.dist-info"))
        os.makedirs(os.path.join(packages_dir, "urllib3-2.0.4.dist-info"))
        # Non-dist-info dirs should be ignored
        os.makedirs(os.path.join(packages_dir, "requests"))

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value=str(tmp_path),
        ):
            result = ProcessGroupPackageService.list_packages("my-group")
            assert len(result) == 2
            # Should be sorted alphabetically by name (case-insensitive)
            assert result[0]["name"] == "requests"
            assert result[0]["version"] == "2.31.0"
            assert result[1]["name"] == "urllib3"
            assert result[1]["version"] == "2.0.4"

    def test_list_packages_handles_missing_version(self, app: Flask, tmp_path: str) -> None:
        packages_dir = os.path.join(str(tmp_path), PACKAGES_DIR_NAME)
        os.makedirs(packages_dir)
        os.makedirs(os.path.join(packages_dir, "mypackage.dist-info"))

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value=str(tmp_path),
        ):
            result = ProcessGroupPackageService.list_packages("my-group")
            assert len(result) == 1
            assert result[0]["name"] == "mypackage"
            assert result[0]["version"] == "unknown"

    # --- _validate_package_name ---

    def test_validate_accepts_simple_names(self, app: Flask) -> None:
        # Should not raise
        ProcessGroupPackageService._validate_package_name("requests")
        ProcessGroupPackageService._validate_package_name("my-package")
        ProcessGroupPackageService._validate_package_name("my_package")
        ProcessGroupPackageService._validate_package_name("package123")

    def test_validate_accepts_version_specifiers(self, app: Flask) -> None:
        ProcessGroupPackageService._validate_package_name("requests==2.31.0")
        ProcessGroupPackageService._validate_package_name("requests>=2.0")
        ProcessGroupPackageService._validate_package_name("requests!=2.30.0")
        ProcessGroupPackageService._validate_package_name("requests~=2.31")

    def test_validate_rejects_dangerous_input(self, app: Flask) -> None:
        with pytest.raises(ApiError, match="Invalid package name"):
            ProcessGroupPackageService._validate_package_name("requests; rm -rf /")
        with pytest.raises(ApiError, match="Invalid package name"):
            ProcessGroupPackageService._validate_package_name("$(whoami)")
        with pytest.raises(ApiError, match="Invalid package name"):
            ProcessGroupPackageService._validate_package_name("")
        with pytest.raises(ApiError, match="Invalid package name"):
            ProcessGroupPackageService._validate_package_name("-malicious")

    # --- install_package ---

    @patch("spiffworkflow_backend.services.process_group_package_service.subprocess.run")
    def test_install_package_calls_uv_pip(self, mock_run: MagicMock, app: Flask, tmp_path: str) -> None:
        mock_run.return_value = MagicMock(stdout="Successfully installed requests-2.31.0")
        packages_dir = os.path.join(str(tmp_path), PACKAGES_DIR_NAME)

        with (
            patch(
                "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
                return_value=str(tmp_path),
            ),
            patch.object(ProcessGroupPackageService, "_ensure_gitignore"),
        ):
            # Create dist-info so list_packages finds it
            os.makedirs(packages_dir, exist_ok=True)
            os.makedirs(os.path.join(packages_dir, "requests-2.31.0.dist-info"))

            result = ProcessGroupPackageService.install_package("my-group", "requests")

        mock_run.assert_called_once_with(
            ["uv", "pip", "install", "--target", packages_dir, "requests"],
            capture_output=True,
            text=True,
            timeout=120,
            check=True,
        )
        assert result["name"] == "requests"
        assert result["version"] == "2.31.0"
        assert result["ok"] is True

    @patch("spiffworkflow_backend.services.process_group_package_service.subprocess.run")
    def test_install_package_raises_on_failure(self, mock_run: MagicMock, app: Flask, tmp_path: str) -> None:
        import subprocess

        mock_run.side_effect = subprocess.CalledProcessError(1, "uv", stderr="No matching distribution")

        with (
            patch(
                "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
                return_value=str(tmp_path),
            ),
            patch.object(ProcessGroupPackageService, "_ensure_gitignore"),
        ):
            with pytest.raises(ApiError, match="Failed to install"):
                ProcessGroupPackageService.install_package("my-group", "nonexistent-pkg-xyz")

    @patch("spiffworkflow_backend.services.process_group_package_service.subprocess.run")
    def test_install_package_raises_on_timeout(self, mock_run: MagicMock, app: Flask, tmp_path: str) -> None:
        import subprocess

        mock_run.side_effect = subprocess.TimeoutExpired("uv", 120)

        with (
            patch(
                "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
                return_value=str(tmp_path),
            ),
            patch.object(ProcessGroupPackageService, "_ensure_gitignore"),
        ):
            with pytest.raises(ApiError, match="timed out"):
                ProcessGroupPackageService.install_package("my-group", "huge-package")

    def test_install_package_rejects_invalid_name(self, app: Flask) -> None:
        with pytest.raises(ApiError, match="Invalid package name"):
            ProcessGroupPackageService.install_package("my-group", "bad; command")

    # --- uninstall_package ---

    @patch("spiffworkflow_backend.services.process_group_package_service.subprocess.run")
    def test_uninstall_package_calls_uv_pip(self, mock_run: MagicMock, app: Flask, tmp_path: str) -> None:
        packages_dir = os.path.join(str(tmp_path), PACKAGES_DIR_NAME)
        os.makedirs(packages_dir)

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value=str(tmp_path),
        ):
            ProcessGroupPackageService.uninstall_package("my-group", "requests")

        mock_run.assert_called_once_with(
            ["uv", "pip", "uninstall", "--target", packages_dir, "requests"],
            capture_output=True,
            text=True,
            timeout=60,
            check=True,
        )

    def test_uninstall_package_raises_when_no_packages_dir(self, app: Flask) -> None:
        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value="/nonexistent",
        ):
            with pytest.raises(ApiError, match="No packages directory"):
                ProcessGroupPackageService.uninstall_package("my-group", "requests")

    @patch("spiffworkflow_backend.services.process_group_package_service.subprocess.run")
    def test_uninstall_package_raises_on_failure(self, mock_run: MagicMock, app: Flask, tmp_path: str) -> None:
        import subprocess

        packages_dir = os.path.join(str(tmp_path), PACKAGES_DIR_NAME)
        os.makedirs(packages_dir)
        mock_run.side_effect = subprocess.CalledProcessError(1, "uv", stderr="Package not found")

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.full_path_from_id",
            return_value=str(tmp_path),
        ):
            with pytest.raises(ApiError, match="Failed to uninstall"):
                ProcessGroupPackageService.uninstall_package("my-group", "requests")

    # --- collect_package_dirs_for_process_model ---

    def test_collect_package_dirs_returns_existing_dirs(self, app: Flask, tmp_path: str) -> None:
        # Set up: group_a/group_b/model — only group_a has .packages/
        group_a = os.path.join(str(tmp_path), "group_a")
        group_b = os.path.join(str(tmp_path), "group_a", "group_b")
        os.makedirs(group_b)
        pkg_dir_a = os.path.join(group_a, PACKAGES_DIR_NAME)
        os.makedirs(pkg_dir_a)

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.ancestor_group_directories",
            return_value=[
                ("group_a", group_a),
                ("group_a/group_b", group_b),
            ],
        ):
            result = ProcessGroupPackageService.collect_package_dirs_for_process_model("group_a/group_b/model")
            assert result == [pkg_dir_a]

    def test_collect_package_dirs_returns_empty_when_none_exist(self, app: Flask) -> None:
        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.ancestor_group_directories",
            return_value=[
                ("group_a", "/nonexistent/group_a"),
            ],
        ):
            result = ProcessGroupPackageService.collect_package_dirs_for_process_model("group_a/model")
            assert result == []

    def test_collect_package_dirs_preserves_outermost_first_order(self, app: Flask, tmp_path: str) -> None:
        # Both ancestor groups have .packages/
        group_a = os.path.join(str(tmp_path), "a")
        group_ab = os.path.join(str(tmp_path), "a", "b")
        os.makedirs(os.path.join(group_a, PACKAGES_DIR_NAME))
        os.makedirs(os.path.join(group_ab, PACKAGES_DIR_NAME))

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.ancestor_group_directories",
            return_value=[
                ("a", group_a),
                ("a/b", group_ab),
            ],
        ):
            result = ProcessGroupPackageService.collect_package_dirs_for_process_model("a/b/model")
            assert len(result) == 2
            # Outermost first
            assert result[0] == os.path.join(group_a, PACKAGES_DIR_NAME)
            assert result[1] == os.path.join(group_ab, PACKAGES_DIR_NAME)

    # --- _ensure_gitignore ---

    def test_ensure_gitignore_creates_entry(self, app: Flask, tmp_path: str) -> None:
        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.root_path",
            return_value=str(tmp_path),
        ):
            ProcessGroupPackageService._ensure_gitignore()
            gitignore_path = os.path.join(str(tmp_path), ".gitignore")
            with open(gitignore_path) as f:
                contents = f.read()
            assert ".packages" in contents

    def test_ensure_gitignore_does_not_duplicate(self, app: Flask, tmp_path: str) -> None:
        gitignore_path = os.path.join(str(tmp_path), ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write(".packages\n")

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.root_path",
            return_value=str(tmp_path),
        ):
            ProcessGroupPackageService._ensure_gitignore()
            with open(gitignore_path) as f:
                contents = f.read()
            # Should appear exactly once
            assert contents.count(".packages") == 1

    def test_ensure_gitignore_appends_to_existing_file(self, app: Flask, tmp_path: str) -> None:
        gitignore_path = os.path.join(str(tmp_path), ".gitignore")
        with open(gitignore_path, "w") as f:
            f.write("*.pyc\n__pycache__/\n")

        with patch(
            "spiffworkflow_backend.services.process_group_package_service.FileSystemService.root_path",
            return_value=str(tmp_path),
        ):
            ProcessGroupPackageService._ensure_gitignore()
            with open(gitignore_path) as f:
                contents = f.read()
            assert "*.pyc" in contents
            assert ".packages" in contents
