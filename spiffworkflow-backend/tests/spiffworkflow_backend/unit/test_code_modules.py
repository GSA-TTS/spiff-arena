from flask.app import Flask
from starlette.testclient import TestClient

from spiffworkflow_backend.services.console_output_service import console_capture
from spiffworkflow_backend.services.process_instance_processor import CodeModuleBasedScriptEngineEnvironment
from spiffworkflow_backend.services.process_instance_processor import ProcessInstanceProcessor
from tests.spiffworkflow_backend.helpers.base_test import BaseTest
from tests.spiffworkflow_backend.helpers.test_data import load_test_spec


class TestCodeModules(BaseTest):
    def test_script_task_can_call_code_module_function(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/code_modules",
            process_model_source_directory="code-modules",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        processor.do_engine_steps(save=True)
        assert processor.get_data()["result"] == 35

    def test_print_output_captured_during_script_execution(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        process_model = load_test_spec(
            "test_group/console_output",
            process_model_source_directory="console-output",
            bpmn_file_name="console_output_test.bpmn",
        )
        process_instance = self.create_process_instance_from_process_model(process_model)
        processor = ProcessInstanceProcessor(process_instance)
        with console_capture() as buf:
            processor.do_engine_steps(save=True)
            lines = buf.drain()
        assert any("hello from script" in line for line in lines)

    def test_model_level_function_can_call_group_level_function(
        self,
        app: Flask,
        client: TestClient,
        with_db_and_bpmn_file_cleanup: None,
    ) -> None:
        """Model-level code module functions should be able to call group-level functions."""
        env = CodeModuleBasedScriptEngineEnvironment(
            environment_globals={},
            code_modules={
                "group_utils": "def add_numbers(a, b):\n    return a + b\n",
                "model_scripts": (
                    "def my_pre_script(task_data):\n"
                    "    task_data['result'] = add_numbers(3, 5)\n"
                ),
            },
        )
        context: dict = {}
        env.execute("my_pre_script(locals())", context)
        assert context["result"] == 8
