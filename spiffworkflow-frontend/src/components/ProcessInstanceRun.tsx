import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  Button,
  ButtonGroup,
  ClickAwayListener,
  Grow,
  MenuItem,
  MenuList,
  Paper,
  Popper,
} from '@mui/material';
import { ArrowDropDown } from '@mui/icons-material';
import { Can } from '@casl/react';
import { useRef, useState } from 'react';
import {
  PermissionsToCheck,
  ProcessInstance,
  ProcessModel,
  RecentProcessModel,
} from '../interfaces';
import HttpService from '../services/HttpService';
import { setLastProcessInstanceRunLocation } from '../services/LocalStorageService';
import { modifyProcessIdentifierForPathParam } from '../helpers';
import { usePermissionFetcher } from '../hooks/PermissionService';
import useAPIError from '../hooks/UseApiError';

const storeRecentProcessModelInLocalStorage = (
  processModelForStorage: ProcessModel,
) => {
  // All values stored in localStorage are strings.
  // Grab our recentProcessModels string from localStorage.
  const stringFromLocalStorage = window.localStorage.getItem(
    'recentProcessModels',
  );

  // adapted from https://stackoverflow.com/a/59424458/6090676
  // If that value is null (meaning that we've never saved anything to that spot in localStorage before), use an empty array as our array. Otherwise, use the value we parse out.
  let array: RecentProcessModel[] = [];
  if (stringFromLocalStorage !== null) {
    // Then parse that string into an actual value.
    array = JSON.parse(stringFromLocalStorage);
  }

  // Here's the value we want to add
  const value = {
    processModelIdentifier: processModelForStorage.id,
    processModelDisplayName: processModelForStorage.display_name,
  };

  // anything with a processGroupIdentifier is old and busted. leave it behind.
  array = array.filter((item) => item.processGroupIdentifier === undefined);

  // If our parsed/empty array doesn't already have this value in it...
  const matchingItem = array.find(
    (item) => item.processModelIdentifier === value.processModelIdentifier,
  );
  if (matchingItem === undefined) {
    // add the value to the beginning of the array
    array.unshift(value);

    // Keep the array to 3 items
    if (array.length > 3) {
      array.pop();
    }
  }

  // once the old and busted serializations are gone, we can put these two statements inside the above if statement

  // turn the array WITH THE NEW VALUE IN IT into a string to prepare it to be stored in localStorage
  const stringRepresentingArray = JSON.stringify(array);

  // and store it in localStorage as "recentProcessModels"
  window.localStorage.setItem('recentProcessModels', stringRepresentingArray);
};

type OwnProps = {
  processModel: ProcessModel;
  className?: string;
  checkPermissions?: boolean;
  buttonText?: string;
};

export default function ProcessInstanceRun({
  processModel,
  className,
  checkPermissions = true,
  buttonText = 'Start',
}: OwnProps) {
  const navigate = useNavigate();
  const { t } = useTranslation();
  const { addError, removeError } = useAPIError();
  const [disableStartButton, setDisableStartButton] = useState<boolean>(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const anchorRef = useRef<HTMLDivElement>(null);
  const startWithConsoleRef = useRef(false);

  const modifiedProcessModelId = modifyProcessIdentifierForPathParam(
    processModel.id,
  );

  const processInstanceCreatePath = `/v1.0/process-instances/${modifiedProcessModelId}`;
  let permissionRequestData: PermissionsToCheck = {
    [processInstanceCreatePath]: ['POST'],
  };

  if (!checkPermissions) {
    permissionRequestData = {};
  }

  const { ability } = usePermissionFetcher(permissionRequestData);

  const onProcessInstanceRun = (processInstance: ProcessInstance) => {
    const processInstanceId = processInstance.id;
    setLastProcessInstanceRunLocation(window.location.pathname);

    if (processInstance.process_model_uses_queued_execution) {
      navigate(
        `/process-instances/for-me/${modifiedProcessModelId}/${processInstanceId}/progress`,
      );
    } else {
      let interstitialUrl = `/process-instances/for-me/${modifiedProcessModelId}/${processInstanceId}/interstitial`;
      if (startWithConsoleRef.current) {
        interstitialUrl += '?with_console=true';
        startWithConsoleRef.current = false;
      }
      navigate(interstitialUrl);
    }
  };

  const processModelRun = (processInstance: ProcessInstance) => {
    removeError();
    if (processModel) {
      storeRecentProcessModelInLocalStorage(processModel);
    }
    if (startWithConsoleRef.current) {
      // Skip the run step — let the SSE interstitial stream handle execution
      // so that console output from the very first tasks is captured.
      onProcessInstanceRun(processInstance);
      return;
    }
    HttpService.makeCallToBackend({
      path: `/process-instance-run/${modifiedProcessModelId}/${processInstance.id}`,
      successCallback: onProcessInstanceRun,
      failureCallback: (result: any) => {
        addError(result);
        setDisableStartButton(false);
      },
      httpMethod: 'POST',
    });
  };

  const processInstanceCreateAndRun = (withConsole = false) => {
    removeError();
    setDisableStartButton(true);
    startWithConsoleRef.current = withConsole;
    HttpService.makeCallToBackend({
      path: processInstanceCreatePath,
      successCallback: processModelRun,
      failureCallback: (result: any) => {
        addError(result);
        setDisableStartButton(false);
      },
      httpMethod: 'POST',
    });
  };

  let startButton = null;
  if (processModel.primary_file_name && processModel.is_executable) {
    startButton = (
      <ButtonGroup
        variant="contained"
        ref={anchorRef}
        className={className}
        disabled={disableStartButton}
      >
        <Button
          data-testid="start-process-instance"
          onClick={() => processInstanceCreateAndRun(false)}
          size="medium"
        >
          {buttonText}
        </Button>
        <Button
          size="small"
          onClick={() => setMenuOpen((prev) => !prev)}
          aria-label={t('start_options')}
        >
          <ArrowDropDown />
        </Button>
      </ButtonGroup>
    );
  }

  const dropdownMenu = (
    <Popper
      open={menuOpen}
      anchorEl={anchorRef.current}
      transition
      sx={{ zIndex: 1400 }}
    >
      {({ TransitionProps, placement }) => (
        <Grow
          {...TransitionProps}
          style={{
            transformOrigin:
              placement === 'bottom' ? 'center top' : 'center bottom',
          }}
        >
          <Paper>
            <ClickAwayListener onClickAway={() => setMenuOpen(false)}>
              <MenuList autoFocusItem>
                <MenuItem
                  onClick={() => {
                    setMenuOpen(false);
                    processInstanceCreateAndRun(true);
                  }}
                >
                  {t('start_with_console')}
                </MenuItem>
              </MenuList>
            </ClickAwayListener>
          </Paper>
        </Grow>
      )}
    </Popper>
  );

  // if checkPermissions is false then assume the page using this component has already checked the permissions
  if (checkPermissions) {
    return (
      <Can I="POST" a={processInstanceCreatePath} ability={ability}>
        {startButton}
        {dropdownMenu}
      </Can>
    );
  }
  return (
    <>
      {startButton}
      {dropdownMenu}
    </>
  );
}
