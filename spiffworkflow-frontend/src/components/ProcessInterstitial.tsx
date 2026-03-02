import React, { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { fetchEventSource } from '@microsoft/fetch-event-source';
import { Alert, Box, Button, CircularProgress, Stack } from '@mui/material';
import { BACKEND_BASE_URL } from '../config';
import HttpService, { getBasicHeaders } from '../services/HttpService';

import InstructionsForEndUser from './InstructionsForEndUser';
import CustomForm from './CustomForm';
import ConsolePanel from './ConsolePanel';
import { ProcessInstance, ProcessInstanceTask, Task } from '../interfaces';
import useAPIError from '../hooks/UseApiError';
import useTaskNavigation from '../hooks/useTaskNavigation';
import {
  HUMAN_TASK_TYPES,
  recursivelyChangeNullAndUndefined,
} from '../helpers';
import { getAndRemoveLastProcessInstanceRunLocation } from '../services/LocalStorageService';

type OwnProps = {
  processInstanceId: number;
  processInstanceShowPageUrl: string;
  allowRedirect: boolean;
  smallSpinner?: boolean;
  collapsableInstructions?: boolean;
  executeTasks?: boolean;
  withConsole?: boolean;
};

export default function ProcessInterstitial({
  processInstanceId,
  allowRedirect,
  processInstanceShowPageUrl,
  smallSpinner = false,
  collapsableInstructions = false,
  executeTasks = true,
  withConsole = false,
}: OwnProps) {
  const [data, setData] = useState<any[]>([]);
  const [lastTask, setLastTask] = useState<any>(null);
  const [state, setState] = useState<string>('RUNNING');
  const [isFadingOut, setIsFadingOut] = useState<boolean>(false);
  const [processInstance, setProcessInstance] =
    useState<ProcessInstance | null>(null);
  const [consoleLines, setConsoleLines] = useState<string[]>([]);
  const [activeHumanTask, setActiveHumanTask] = useState<Task | null>(null);
  const [inlineTaskData, setInlineTaskData] = useState<any>(null);
  const [formButtonsDisabled, setFormButtonsDisabled] = useState(false);
  const [sseGeneration, setSseGeneration] = useState(0);

  const navigate = useNavigate();
  const { t } = useTranslation();
  const { addError, removeError } = useAPIError();

  const {
    canGoBack,
    canGoForward,
    goBack,
    goForward,
    loading: navLoading,
  } = useTaskNavigation(processInstanceId, activeHumanTask?.guid);

  useEffect(() => {
    const abortController = new AbortController();
    setState('RUNNING');
    setLastTask(null);
    setData([]);

    let sseUrl = `${BACKEND_BASE_URL}/tasks/${processInstanceId}?execute_tasks=${executeTasks}`;
    if (withConsole) {
      sseUrl += '&with_console=true';
    }
    fetchEventSource(sseUrl, {
      headers: getBasicHeaders(),
      signal: abortController.signal,
      onmessage(ev) {
        const retValue = JSON.parse(ev.data);
        if (retValue.type === 'error') {
          addError(retValue.error);
        } else if (retValue.type === 'task') {
          setData((prevData) => [retValue.task, ...prevData]);
          setLastTask(retValue.task);
        } else if (retValue.type === 'unrunnable_instance') {
          setProcessInstance(retValue.unrunnable_instance);
        } else if (retValue.type === 'console') {
          setConsoleLines((prev) => [...prev, ...retValue.console.lines]);
        }
      },
      onerror(error: any) {
        if (abortController.signal.aborted) {
          return;
        }
        setState('CLOSED');
        const wasAbortedError = /\baborted\b/.test(error.message);
        if (!wasAbortedError) {
          addError(error);
          throw error;
        }
      },
      onclose() {
        if (abortController.signal.aborted) {
          return;
        }
        setState('CLOSED');
      },
    });
    return () => abortController.abort();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [sseGeneration]);

  const shouldRedirectToTask = useCallback(
    (myTask: ProcessInstanceTask): boolean => {
      return (
        allowRedirect &&
        !processInstance &&
        myTask &&
        myTask.can_complete &&
        HUMAN_TASK_TYPES.includes(myTask.type)
      );
    },
    [allowRedirect, processInstance],
  );

  const shouldRedirectToProcessInstance = useCallback((): boolean => {
    return allowRedirect && state === 'CLOSED';
  }, [allowRedirect, state]);

  const loadTaskInline = useCallback(
    (taskProcessInstanceId: number, taskGuid: string) => {
      let taskUrl = `/tasks/${taskProcessInstanceId}/${taskGuid}?with_form_data=true`;
      if (withConsole) {
        taskUrl += '&with_console=true';
      }
      HttpService.makeCallToBackend({
        path: taskUrl,
        successCallback: (result: any) => {
          if (result.console_lines && result.console_lines.length > 0) {
            setConsoleLines((prev: string[]) => [
              ...prev,
              ...result.console_lines,
            ]);
          }
          setActiveHumanTask(result);
          const variableName = result.extensions?.variableName;
          let taskDataToUse;
          if (result.saved_form_data) {
            taskDataToUse = result.saved_form_data;
          } else if (
            typeof variableName !== 'undefined' &&
            variableName != null &&
            typeof result.data[variableName] !== 'undefined'
          ) {
            taskDataToUse = result.data[variableName];
          } else {
            taskDataToUse = result.data;
          }
          setInlineTaskData(
            recursivelyChangeNullAndUndefined(taskDataToUse, undefined),
          );
          setFormButtonsDisabled(false);
        },
        failureCallback: (error: any) => {
          addError(error);
          setFormButtonsDisabled(false);
        },
      });
    },
    [addError, withConsole],
  );

  useEffect(() => {
    // Added this separate use effect so that the timer interval will be cleared if
    // we end up redirecting back to the TaskShow page.
    if (shouldRedirectToTask(lastTask)) {
      if (withConsole) {
        // Don't redirect — fetch full task data and render form inline
        if (!activeHumanTask) {
          loadTaskInline(lastTask.process_instance_id, lastTask.id);
        }
        return undefined;
      }
      lastTask.properties.instructionsForEndUser = '';
      const timerId = setInterval(() => {
        const taskUrl = `/tasks/${lastTask.process_instance_id}/${lastTask.id}`;
        navigate(taskUrl);
      }, 500);
      return () => clearInterval(timerId);
    }
    if (shouldRedirectToProcessInstance()) {
      setIsFadingOut(true);
      // Clean up console mode preference since the process is done
      localStorage.removeItem(`console_mode_${processInstanceId}`);
      setTimeout(() => {
        localStorage.setItem(
          'lastProcessInstanceId',
          processInstanceId.toString(),
        );
        const toUrl =
          getAndRemoveLastProcessInstanceRunLocation() ??
          processInstanceShowPageUrl;
        navigate(toUrl);
      }, 4000); // Adjust the timeout to match the CSS transition duration
    }
    return undefined;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [
    lastTask,
    navigate,
    processInstanceId,
    processInstanceShowPageUrl,
    shouldRedirectToProcessInstance,
    shouldRedirectToTask,
    state,
    withConsole,
  ]);

  const getLoadingIcon = () => {
    if (state === 'RUNNING') {
      let style = { margin: '50px 0 50px 50px' };
      if (smallSpinner) {
        style = { margin: '2x 5px 2px 2px' };
      }
      return <CircularProgress style={style} />;
    }
    return null;
  };

  const inlineMessage = (
    title: string,
    subtitle: string,
    kind: 'info' | 'warning' | 'error' = 'info',
  ) => {
    return (
      <div>
        <Alert severity={kind} title={title}>
          {subtitle}
        </Alert>
      </div>
    );
  };

  const userMessageForProcessInstance = (
    pi: ProcessInstance,
    myTask: ProcessInstanceTask | null = null,
  ) => {
    if (['terminated', 'suspended'].includes(pi.status)) {
      return inlineMessage(
        t('process_status', { status: pi.status }),
        t('process_status_message', { status: pi.status }),
        'warning',
      );
    }
    if (pi.status === 'error') {
      let errMessage = t('process_error_msg');
      if (myTask?.error_message) {
        errMessage = errMessage.concat(myTask.error_message);
      }
      return inlineMessage(t('process_error'), errMessage, 'error');
    }
    // Otherwise we are not started, waiting, complete, or user_input_required
    const defaultMsg = t('no_additional_instructions');
    if (myTask) {
      return (
        <InstructionsForEndUser
          task={myTask}
          defaultMessage={defaultMsg}
          allowCollapse={collapsableInstructions}
        />
      );
    }
    return inlineMessage(t('process_error'), defaultMsg, 'info');
  };

  const userMessage = (myTask: ProcessInstanceTask) => {
    if (processInstance) {
      return userMessageForProcessInstance(processInstance, myTask);
    }

    if (!myTask.can_complete && HUMAN_TASK_TYPES.includes(myTask.type)) {
      let message = t('task_assigned_different_person');
      if (myTask.assigned_user_group_identifier) {
        message = t('task_assigned_group', {
          group: myTask.assigned_user_group_identifier,
        });
      } else if (myTask.potential_owner_usernames) {
        let potentialOwnerArray = myTask.potential_owner_usernames.split(',');
        if (potentialOwnerArray.length > 2) {
          potentialOwnerArray = potentialOwnerArray.slice(0, 2).concat(['...']);
        }
        message = t('task_assigned_users', {
          users: potentialOwnerArray.join(', '),
        });
      }

      return inlineMessage('', `${message} ${t('no_action_required')}`);
    }
    if (shouldRedirectToTask(myTask)) {
      if (withConsole) {
        return getLoadingIcon();
      }
      return inlineMessage('', t('redirecting'));
    }
    if (myTask?.can_complete && HUMAN_TASK_TYPES.includes(myTask.type)) {
      return inlineMessage(
        '',
        t('task_ready_for_completion', { taskTitle: myTask.title }),
      );
    }
    if (myTask.error_message) {
      return inlineMessage(t('error'), myTask.error_message, 'error');
    }
    return (
      <div>
        <InstructionsForEndUser
          task={myTask}
          defaultMessage={t('no_instructions_for_task')}
          allowCollapse={collapsableInstructions}
        />
      </div>
    );
  };

  /** In the event there is no task information and the connection closed,
   * redirect to the home page. */
  if (state === 'CLOSED' && lastTask === null && allowRedirect) {
    // Favor redirecting to the process instance show page
    if (processInstance) {
      const toUrl =
        getAndRemoveLastProcessInstanceRunLocation() ??
        processInstanceShowPageUrl;
      navigate(toUrl);
    } else {
      const taskUrl = '/tasks';
      navigate(taskUrl);
    }
  }

  let displayableData = data;
  if (state === 'CLOSED') {
    displayableData = [data[0]];
  }

  const className = (index: number) => {
    if (displayableData.length === 1) {
      return 'user_instructions';
    }
    return index < 4 ? `user_instructions_${index}` : `user_instructions_4`;
  };

  const handleGoBack = async () => {
    if (formButtonsDisabled || navLoading) {
      return;
    }
    setFormButtonsDisabled(true);
    const newTaskGuid = await goBack();
    if (newTaskGuid) {
      if (withConsole) {
        setActiveHumanTask(null);
        setInlineTaskData(null);
        loadTaskInline(processInstanceId, newTaskGuid);
      } else {
        navigate(`/tasks/${processInstanceId}/${newTaskGuid}`);
      }
    } else {
      setFormButtonsDisabled(false);
    }
  };

  const handleGoForward = async () => {
    if (formButtonsDisabled || navLoading || !inlineTaskData) {
      return;
    }
    setFormButtonsDisabled(true);
    removeError();
    const dataToSubmit = recursivelyChangeNullAndUndefined(
      { ...inlineTaskData },
      null,
    );
    delete dataToSubmit.isManualTask;
    const result = await goForward(dataToSubmit);
    if (result && result.process_instance_id && result.id) {
      if (withConsole) {
        setActiveHumanTask(null);
        setInlineTaskData(null);
        loadTaskInline(result.process_instance_id, result.id);
      } else {
        navigate(`/tasks/${result.process_instance_id}/${result.id}`);
      }
    } else {
      setFormButtonsDisabled(false);
    }
  };

  const handleInlineFormSubmit = (formObject: any, _event: any) => {
    if (formButtonsDisabled || !activeHumanTask) {
      return;
    }

    const dataToSubmit = formObject?.formData;
    if (!dataToSubmit) {
      return;
    }

    setFormButtonsDisabled(true);
    removeError();
    delete dataToSubmit.isManualTask;
    recursivelyChangeNullAndUndefined(dataToSubmit, null);

    HttpService.makeCallToBackend({
      path: `/tasks/${activeHumanTask.process_instance_id}/${activeHumanTask.guid}?with_console=true`,
      httpMethod: 'PUT',
      postBody: dataToSubmit,
      successCallback: (result: any) => {
        if (result.console_lines) {
          setConsoleLines((prev) => [...prev, ...result.console_lines]);
        }
        setActiveHumanTask(null);
        setInlineTaskData(null);
        setFormButtonsDisabled(false);
        setLastTask(null);
        setData([]);
        setState('RUNNING');
        setSseGeneration((prev) => prev + 1);
      },
      failureCallback: (error: any) => {
        addError(error);
        setFormButtonsDisabled(false);
      },
    });
  };

  const inlineFormElement = () => {
    if (!activeHumanTask) {
      return null;
    }

    let formUiSchema;
    let jsonSchema = activeHumanTask.form_schema;

    if (activeHumanTask.typename !== 'UserTask') {
      jsonSchema = {
        type: 'object',
        required: [],
        properties: {
          isManualTask: {
            type: 'boolean',
            title: 'Is ManualTask',
            default: true,
          },
        },
      };
      formUiSchema = {
        isManualTask: {
          'ui:widget': 'hidden',
        },
      };
    } else if (activeHumanTask.form_ui_schema) {
      formUiSchema = activeHumanTask.form_ui_schema;
    }

    let submitButtonText = t('submit');
    if (activeHumanTask.typename === 'ManualTask') {
      submitButtonText = t('continue');
    } else if (formUiSchema) {
      const submitButtonOptions =
        formUiSchema['ui:submitButtonOptions'] ||
        formUiSchema['ui:options']?.submitButtonOptions ||
        {};
      if ('submitText' in submitButtonOptions) {
        submitButtonText = submitButtonOptions.submitText as string;
      }
    }

    return (
      <Box className="limited-width-for-readability">
        <CustomForm
          id={`inline-form-${activeHumanTask.guid}`}
          key={`inline-form-${activeHumanTask.guid}`}
          disabled={formButtonsDisabled}
          formData={inlineTaskData}
          onChange={(obj: any) => setInlineTaskData(obj.formData)}
          onSubmit={handleInlineFormSubmit}
          schema={jsonSchema}
          uiSchema={formUiSchema}
        >
          <Stack direction="row" spacing={2}>
            {canGoBack && (
              <Button
                id="back-button"
                onClick={handleGoBack}
                disabled={formButtonsDisabled || navLoading}
                variant="outlined"
              >
                {t('back')}
              </Button>
            )}
            <Button
              type="submit"
              id="submit-button"
              disabled={formButtonsDisabled}
              variant="contained"
            >
              {submitButtonText}
            </Button>
            {canGoForward && (
              <Button
                id="forward-button"
                onClick={handleGoForward}
                disabled={formButtonsDisabled || navLoading}
                variant="outlined"
              >
                {t('forward')}
              </Button>
            )}
          </Stack>
        </CustomForm>
      </Box>
    );
  };

  const innerComponents = () => {
    if (activeHumanTask) {
      return (
        <>
          <InstructionsForEndUser
            task={activeHumanTask}
            className="with-bottom-margin"
          />
          {inlineFormElement()}
        </>
      );
    }
    if (lastTask) {
      return (
        <>
          {getLoadingIcon()}
          {displayableData.map((d, index) => (
            <div className={className(index)}>{userMessage(d)}</div>
          ))}
        </>
      );
    }
    if (processInstance) {
      return (
        <>
          {getLoadingIcon()}
          {userMessageForProcessInstance(processInstance)}
        </>
      );
    }
    return getLoadingIcon();
  };
  return (
    <Box
      className={isFadingOut ? 'fade-out' : ''}
      component="main"
      sx={{
        flexGrow: 1,
        p: 3,
        overflow: 'auto',
      }}
    >
      {innerComponents()}
      {withConsole && (
        <ConsolePanel
          lines={consoleLines}
          onClear={() => setConsoleLines([])}
        />
      )}
    </Box>
  );
}
