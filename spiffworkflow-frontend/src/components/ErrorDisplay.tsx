import { Notification } from './Notification';
import useAPIError from '../hooks/UseApiError';
import { ErrorForDisplay } from '../interfaces';

function errorDetailDisplay(
  errorObject: any,
  propertyName: string,
  title: string
) {
  // Creates a bit of html for displaying a single error property if it exists.
  if (propertyName in errorObject && errorObject[propertyName]) {
    return (
      <div className="error_info">
        <span className="error_title">{title}:</span>
        {errorObject[propertyName]}
      </div>
    );
  }
  return null;
}

export const childrenForErrorObject = (errorObject: ErrorForDisplay) => {
  let sentryLinkTag = null;
  if (errorObject.sentry_link) {
    sentryLinkTag = (
      <span>
        {
          ': Find details about this error here (it may take a moment to become available): '
        }
        <a href={errorObject.sentry_link} target="_blank" rel="noreferrer">
          {errorObject.sentry_link}
        </a>
      </span>
    );
  }

  const message = <div>{errorObject.message}</div>;
  const taskName = errorDetailDisplay(errorObject, 'task_name', 'Task Name');
  const taskId = errorDetailDisplay(errorObject, 'task_id', 'Task ID');
  const fileName = errorDetailDisplay(errorObject, 'file_name', 'File Name');
  const lineNumber = errorDetailDisplay(
    errorObject,
    'line_number',
    'Line Number'
  );
  const errorLine = errorDetailDisplay(errorObject, 'error_line', 'Context');
  let taskTrace = null;
  if (errorObject.task_trace && errorObject.task_trace.length > 0) {
    taskTrace = (
      <div className="error_info">
        <span className="error_title">Call Activity Trace:</span>
        {errorObject.task_trace.reverse().join(' -> ')}
      </div>
    );
  }

  return [
    message,
    <br />,
    sentryLinkTag,
    taskName,
    taskId,
    fileName,
    lineNumber,
    errorLine,
    taskTrace,
  ];
};

export default function ErrorDisplay() {
  const errorObject = useAPIError().error;
  const { removeError } = useAPIError();
  let errorTag = null;

  if (errorObject) {
    const title = 'Error:';

    errorTag = (
      <Notification title={title} onClose={() => removeError()} type="error">
        <>{childrenForErrorObject(errorObject)}</>
      </Notification>
    );
  }

  return errorTag;
}
