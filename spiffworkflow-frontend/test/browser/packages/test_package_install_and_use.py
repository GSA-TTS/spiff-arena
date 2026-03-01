import os
import re
import uuid

from playwright.sync_api import Page, expect

from helpers.login import login, logout, BASE_URL
from helpers.process_model import delete_process_model


FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_install_package_and_use_in_script_task(page: Page):
    """
    End-to-end test: install pandas in a process group, upload a BPMN
    with a pandas script task, run it, and verify it completes.
    """

    unique = uuid.uuid4().hex
    group_id = f"test-pkg-{unique}"
    group_name = f"Test Pkg {unique}"
    model_id = f"test-pandas-{unique}"
    model_name = f"Test Pandas {unique}"

    # 1. Login
    login(page)

    # 2. Create a new process group
    page.goto(f"{BASE_URL}/process-groups")
    add_group_btn = page.locator(
        'a[data-testid="add-process-group-button"][href$="/new"]'
    )
    expect(add_group_btn).to_be_visible(timeout=20000)
    add_group_btn.click()
    expect(page).to_have_url(re.compile(r"/process-groups/new$"), timeout=10000)

    display_input = page.locator("#process-group-display-name")
    expect(display_input).to_be_visible()
    display_input.fill(group_name)

    id_input = page.locator("#process-group-identifier")
    expect(id_input).to_be_visible()
    id_input.fill(group_id)

    page.get_by_role("button", name="Submit").click()
    expect(page).to_have_url(
        re.compile(rf"/process-groups/{re.escape(group_id)}$"), timeout=10000
    )

    # 3. Install pandas on the group edit page
    edit_btn = page.get_by_test_id("edit-process-group-button")
    expect(edit_btn).to_be_visible()
    edit_btn.click()
    expect(page).to_have_url(
        re.compile(rf"/process-groups/{re.escape(group_id)}/edit$"), timeout=10000
    )

    # Fill the package name and install
    pkg_input = page.get_by_test_id("package-name-input-field")
    expect(pkg_input).to_be_visible(timeout=10000)
    pkg_input.fill("pandas")

    install_btn = page.get_by_test_id("install-package-button")
    expect(install_btn).to_be_enabled()
    install_btn.click()

    # Wait for pandas to appear in the installed list (can take a while)
    expect(page.get_by_test_id("package-list-item-pandas")).to_be_visible(
        timeout=180000
    )

    # Submit the group edit form to save and return to group page
    page.get_by_role("button", name="Submit").click()
    expect(page).to_have_url(
        re.compile(rf"/process-groups/{re.escape(group_id)}$"), timeout=10000
    )

    # 4. Create a new process model in the group
    add_model_btn = page.get_by_test_id("add-process-model-button")
    expect(add_model_btn).to_be_visible(timeout=10000)
    add_model_btn.click()
    expect(page).to_have_url(
        re.compile(rf"/process-models/{re.escape(group_id)}/new$"), timeout=10000
    )

    model_display_input = page.locator('input[name="display_name"]')
    expect(model_display_input).to_be_visible()
    model_display_input.fill(model_name)

    model_id_input = page.locator('input[name="id"]')
    expect(model_id_input).to_be_visible()
    model_id_input.fill(model_id)

    page.get_by_role("button", name="Submit").click()

    model_path = f"{group_id}:{model_id}"
    expect(page).to_have_url(
        re.compile(rf"/process-models/{re.escape(model_path)}$"), timeout=10000
    )

    # 5. Upload the BPMN fixture via the UI upload dialog
    #    First switch to the "Files" tab where the Add File dropdown lives
    files_tab = page.get_by_role("tab", name=re.compile(r"Files", re.IGNORECASE))
    expect(files_tab).to_be_visible(timeout=10000)
    files_tab.click()

    #    Open the MUI "Add File" Select dropdown
    add_file_select = page.locator('[aria-labelledby="add-file-select-label"]')
    expect(add_file_select).to_be_visible(timeout=10000)
    add_file_select.click()

    #    Select the "Upload File" option from the dropdown menu
    page.get_by_role("option", name=re.compile(r"Upload File", re.IGNORECASE)).click()

    #    The file upload dialog should appear — set the file on the hidden input
    file_input = page.locator('input[type="file"]')
    expect(file_input).to_be_attached(timeout=10000)
    bpmn_path = os.path.join(FIXTURES_DIR, "pandas_script_test.bpmn")
    file_input.set_input_files(bpmn_path)

    #    Click the Upload button in the dialog
    upload_btn = page.get_by_role("button", name=re.compile(r"^Upload$", re.IGNORECASE))
    expect(upload_btn).to_be_visible(timeout=10000)
    upload_btn.click()

    #    Wait for the upload to complete and the model to refresh.
    #    The BPMN file should be auto-set as primary since it's the first file.
    #    Reload the page to ensure the model state is fully refreshed.
    page.wait_for_timeout(3000)
    page.goto(f"{BASE_URL}/process-models/{model_path}")
    expect(page).to_have_url(
        re.compile(rf"/process-models/{re.escape(model_path)}"), timeout=10000
    )

    # 6. Run the process
    start_btn = page.get_by_test_id("start-process-instance").first
    expect(start_btn).to_be_enabled(timeout=15000)
    start_btn.click()

    # Wait for navigation to process instances / interstitial page
    page.wait_for_url(re.compile(r"/process-instances"), timeout=30000)

    # Give the process time to execute (pandas import may be slow on first run)
    page.wait_for_timeout(10000)

    # Navigate to the process instance to check status.
    # We may be on an interstitial page, instance show page, or instance list.
    # Try to find instance links first.
    instance_link = page.get_by_test_id("process-instance-show-link-id")
    if instance_link.count() > 0:
        instance_link.first.click()
    elif "/process-instances/" in page.url and re.search(r"/process-instances/\d+", page.url):
        # Already on an instance detail page
        pass
    else:
        # Navigate to the all-instances list to find our instance
        page.goto(f"{BASE_URL}/process-instances/all")
        expect(
            page.get_by_test_id("process-instance-show-link-id").first
        ).to_be_visible(timeout=15000)
        page.get_by_test_id("process-instance-show-link-id").first.click()

    # Verify the process instance completed
    expect(
        page.get_by_test_id("process-instance-status-chip").get_by_text("complete")
    ).to_be_visible(timeout=60000)

    # 7. Cleanup: go back to the model page and delete the model
    page.goto(f"{BASE_URL}/process-models/{model_path}")
    expect(page).to_have_url(
        re.compile(rf"/process-models/{re.escape(model_path)}"), timeout=10000
    )
    delete_process_model(page, group_id)

    # Delete the process group
    delete_group_btn = page.get_by_test_id("delete-process-group-button")
    expect(delete_group_btn).to_be_visible(timeout=10000)
    delete_group_btn.click()

    # Confirm deletion dialog
    dialogs = page.get_by_role("dialog")
    expect(dialogs).to_be_visible(timeout=10000)
    delete_confirm_btns = dialogs.locator("button", has_text="Delete")
    for i in range(delete_confirm_btns.count()):
        btn = delete_confirm_btns.nth(i)
        if btn.is_visible():
            btn.click()
            break

    expect(page).to_have_url(re.compile(r"/process-groups$"), timeout=10000)

    # 8. Logout
    logout(page)
