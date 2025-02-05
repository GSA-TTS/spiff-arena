import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { Upload, Edit, TrashCan } from '@carbon/icons-react';
import { Button, Stack } from '@carbon/react';
import { Can } from '@casl/react';
import ProcessBreadcrumb from '../components/ProcessBreadcrumb';
import HttpService from '../services/HttpService';
import useAPIError from '../hooks/UseApiError';

import {
  getGroupFromModifiedModelId,
  modifyProcessIdentifierForPathParam,
  setPageTitle,
} from '../helpers';
import { PermissionsToCheck, ProcessFile, ProcessModel } from '../interfaces';
import ButtonWithConfirmation from '../components/ButtonWithConfirmation';
import { usePermissionFetcher } from '../hooks/PermissionService';
import { useUriListForPermissions } from '../hooks/UriListForPermissions';
import ProcessInstanceRun from '../components/ProcessInstanceRun';
import { Notification } from '../components/Notification';
import ProcessModelTestRun from '../components/ProcessModelTestRun';
import ProcessModelTabs from '../components/ProcessModelTabs';
import ProcessModelFileUploadModal from '../components/ProcessModelFileUploadModal';

export default function ProcessModelShow() {
  const params = useParams();
  const { addError, removeError } = useAPIError();
  const navigate = useNavigate();

  const [processModel, setProcessModel] = useState<ProcessModel | null>(null);
  const [reloadModel, setReloadModel] = useState<boolean>(false);
  const [showFileUploadModal, setShowFileUploadModal] =
    useState<boolean>(false);
  const [processModelPublished, setProcessModelPublished] = useState<any>(null);
  const [publishDisabled, setPublishDisabled] = useState<boolean>(false);
  const [selectedTabIndex, setSelectedTabIndex] = useState<number>(0);
  const [readmeFile, setReadmeFile] = useState<ProcessFile | null>(null);

  const { targetUris } = useUriListForPermissions();
  const permissionRequestData: PermissionsToCheck = {
    [targetUris.processInstanceCreatePath]: ['POST'],
    [targetUris.processInstanceListForMePath]: ['POST'],
    [targetUris.processModelFileCreatePath]: ['POST', 'PUT', 'GET', 'DELETE'],
    [targetUris.processModelPublishPath]: ['POST'],
    [targetUris.processModelShowPath]: ['PUT', 'DELETE'],
    [targetUris.processModelTestsPath]: ['POST'],
  };
  const { ability, permissionsLoaded } = usePermissionFetcher(
    permissionRequestData,
  );

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    `${params.process_model_id}`,
  );

  let hasTestCaseFiles: boolean = false;

  const isTestCaseFile = (processModelFile: ProcessFile) => {
    return processModelFile.name.match(/^test_.*\.json$/);
  };

  if (processModel) {
    hasTestCaseFiles = !!processModel.files.find(
      (processModelFile: ProcessFile) => isTestCaseFile(processModelFile),
    );
  }

  useEffect(() => {
    const processResult = (result: ProcessModel) => {
      setProcessModel(result);
      setReloadModel(false);
      setPageTitle([result.display_name]);

      let newTabIndex = 1;
      let foundReadme = null;
      result.files.forEach((file: ProcessFile) => {
        if (file.name === 'README.md') {
          foundReadme = file;
          newTabIndex = 0;
        }
      });
      setReadmeFile(foundReadme);
      setSelectedTabIndex(newTabIndex);
    };
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}?include_file_references=true`,
      successCallback: processResult,
    });
  }, [reloadModel, modifiedProcessModelId]);

  const onUploadedCallback = () => {
    setReloadModel(true);
  };

  const reloadModelOhYeah = (_httpResult: any) => {
    setReloadModel(!reloadModel);
  };

  const onDeleteFile = (fileName: string) => {
    const url = `/process-models/${modifiedProcessModelId}/files/${fileName}`;
    const httpMethod = 'DELETE';
    HttpService.makeCallToBackend({
      path: url,
      successCallback: reloadModelOhYeah,
      httpMethod,
    });
  };

  const onSetPrimaryFile = (fileName: string) => {
    const url = `/process-models/${modifiedProcessModelId}`;
    const httpMethod = 'PUT';

    const processModelToPass = {
      primary_file_name: fileName,
    };
    HttpService.makeCallToBackend({
      path: url,
      successCallback: onUploadedCallback,
      httpMethod,
      postBody: processModelToPass,
    });
  };

  const navigateToProcessModels = (_result: any) => {
    navigate(
      `/process-groups/${getGroupFromModifiedModelId(modifiedProcessModelId)}`,
    );
  };

  const deleteProcessModel = () => {
    HttpService.makeCallToBackend({
      path: `/process-models/${modifiedProcessModelId}`,
      successCallback: navigateToProcessModels,
      httpMethod: 'DELETE',
    });
  };

  const postPublish = (value: any) => {
    setPublishDisabled(false);
    setProcessModelPublished(value);
  };

  const publishProcessModel = () => {
    setPublishDisabled(true);
    setProcessModelPublished(null);
    HttpService.makeCallToBackend({
      path: targetUris.processModelPublishPath,
      successCallback: postPublish,
      httpMethod: 'POST',
    });
  };

  const doFileUpload = (filesToUpload: File[], forceOverwrite = false) => {
    if (!filesToUpload || filesToUpload.length === 0) {
      return; // No files to upload
    }
    removeError();
    const url = `/process-models/${modifiedProcessModelId}/files`;
    const formData = new FormData();
    formData.append('file', filesToUpload[0]);
    formData.append('fileName', filesToUpload[0].name);
    formData.append('overwrite', forceOverwrite.toString()); // Add overwrite parameter

    HttpService.makeCallToBackend({
      path: url,
      successCallback: onUploadedCallback,
      httpMethod: 'POST',
      postBody: formData,
      failureCallback: addError,
    });
  };

  const handleFileUploadCancel = () => {
    setShowFileUploadModal(false);
  };

  const checkDuplicateFile = (files: File[], forceOverwrite = false) => {
    if (forceOverwrite) {
      doFileUpload(files, true);
    } else {
      doFileUpload(files);
    }
    setShowFileUploadModal(false);
  };

  const updateSelectedTab = (newTabIndex: any) => {
    setSelectedTabIndex(newTabIndex.selectedIndex);
  };

  const processModelPublishMessage = () => {
    if (processModelPublished) {
      const prUrl: string = processModelPublished.pr_url;
      return (
        <Notification
          title="Model Published:"
          onClose={() => setProcessModelPublished(false)}
        >
          <a href={prUrl} target="_void()">
            View the changes and create a Pull Request
          </a>
        </Notification>
      );
    }
    return null;
  };

  if (processModel) {
    const processStartButton = (
      <Stack orientation="horizontal" gap={3}>
        <Can
          I="POST"
          a={targetUris.processInstanceCreatePath}
          ability={ability}
        >
          <>
            <ProcessInstanceRun processModel={processModel} />
          </>
        </Can>
      </Stack>
    );
    return (
      <>
        <ProcessModelFileUploadModal
          showFileUploadModal={showFileUploadModal}
          processModel={processModel}
          onFileUpload={doFileUpload}
          handleFileUploadCancel={handleFileUploadCancel}
          checkDuplicateFile={checkDuplicateFile}
        />
        <ProcessBreadcrumb
          hotCrumbs={[
            ['Process Groups', '/process-groups'],
            {
              entityToExplode: processModel,
              entityType: 'process-model',
            },
          ]}
        />
        {processModelPublishMessage()}
        <Stack orientation="horizontal" gap={1}>
          <h1 className="with-icons">
            Process Model: {processModel.display_name}
          </h1>
          <Can I="PUT" a={targetUris.processModelShowPath} ability={ability}>
            <Button
              kind="ghost"
              data-qa="edit-process-model-button"
              renderIcon={Edit}
              iconDescription="Edit Process Model"
              hasIconOnly
              href={`/process-models/${modifiedProcessModelId}/edit`}
            />
          </Can>
          <Can I="DELETE" a={targetUris.processModelShowPath} ability={ability}>
            <ButtonWithConfirmation
              kind="ghost"
              data-qa="delete-process-model-button"
              renderIcon={TrashCan}
              iconDescription="Delete Process Model"
              hasIconOnly
              description={`Delete process model: ${processModel.display_name}`}
              onConfirmation={deleteProcessModel}
              confirmButtonLabel="Delete"
            />
          </Can>
          {!processModel.actions || processModel.actions.publish ? (
            <Can
              I="POST"
              a={targetUris.processModelPublishPath}
              ability={ability}
            >
              <Button
                kind="ghost"
                data-qa="publish-process-model-button"
                renderIcon={Upload}
                iconDescription="Publish Changes"
                hasIconOnly
                onClick={publishProcessModel}
                disabled={publishDisabled}
              />
            </Can>
          ) : null}
          <Can I="POST" a={targetUris.processModelTestsPath} ability={ability}>
            {hasTestCaseFiles ? (
              <ProcessModelTestRun titleText="Run all BPMN unit tests for this process model" />
            ) : null}
          </Can>
        </Stack>
        <p className="process-description">{processModel.description}</p>
        {processModel.primary_file_name && processModel.is_executable
          ? processStartButton
          : null}

        <br />
        <br />

        <ProcessModelTabs
          processModel={processModel}
          ability={ability}
          targetUris={targetUris}
          modifiedProcessModelId={modifiedProcessModelId}
          selectedTabIndex={selectedTabIndex}
          updateSelectedTab={updateSelectedTab}
          onDeleteFile={onDeleteFile}
          onSetPrimaryFile={onSetPrimaryFile}
          isTestCaseFile={isTestCaseFile}
          readmeFile={readmeFile}
        />
        {permissionsLoaded ? (
          <span data-qa="process-model-show-permissions-loaded" />
        ) : null}
      </>
    );
  }
  return null;
}
