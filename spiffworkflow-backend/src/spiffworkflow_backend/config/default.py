"""Default."""
import re
from os import environ

SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR = environ.get("SPIFFWORKFLOW_BACKEND_BPMN_SPEC_ABSOLUTE_DIR")
cors_allow_all = "*"
SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS = re.split(
    r",\s*", environ.get("SPIFFWORKFLOW_BACKEND_CORS_ALLOW_ORIGINS", default=cors_allow_all)
)

SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER = (
    environ.get("SPIFFWORKFLOW_BACKEND_RUN_BACKGROUND_SCHEDULER", default="false") == "true"
)
SPIFFWORKFLOW_BACKEND_SPIFFWORKFLOW_FRONTEND_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_SPIFFWORKFLOW_FRONTEND_URL", default="http://localhost:7001"
)
SPIFFWORKFLOW_BACKEND_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_URL", default="http://localhost:7000"
)
# service task connector proxy
SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_CONNECTOR_PROXY_URL", default="http://localhost:7004"
)

# Open ID server
SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL = environ.get(
    "SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL",
    default="http://localhost:7002/realms/spiffworkflow"
    # "SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL", default="http://localhost:7000/openid"
)

# Replace above line with this to use the built-in Open ID Server.
# SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL = environ.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_SERVER_URL", default="http://localhost:7000/openid")
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID = environ.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_ID", default="spiffworkflow-backend")
SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY = environ.get(
    "SPIFFWORKFLOW_BACKEND_OPEN_ID_CLIENT_SECRET_KEY", default="JXeQExm0JhQPLumgHtIIqf52bDalHz0q"
)  # noqa: S105

# Tenant specific fields is a comma separated list of field names that we will convert to list of strings
# and store in the user table's tenant_specific_field_n columns. You can have up to three items in this
# comma-separated list.
SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS = environ.get("SPIFFWORKFLOW_BACKEND_OPEN_ID_TENANT_SPECIFIC_FIELDS")

SPIFFWORKFLOW_BACKEND_LOG_TO_FILE = (
    environ.get("SPIFFWORKFLOW_BACKEND_LOG_TO_FILE", default="false") == "true"
)

SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME = environ.get(
    "SPIFFWORKFLOW_BACKEND_PERMISSIONS_FILE_NAME"
)

# Sentry Configuration
SPIFFWORKFLOW_BACKEND_SENTRY_DSN = environ.get("SPIFFWORKFLOW_BACKEND_SENTRY_DSN", default="")
SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE = environ.get(
    "SPIFFWORKFLOW_BACKEND_SENTRY_ERRORS_SAMPLE_RATE", default="1"
)  # send all errors
SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE = environ.get(
    "SPIFFWORKFLOW_BACKEND_SENTRY_TRACES_SAMPLE_RATE", default="0.01"
)  # send 1% of traces

SPIFFWORKFLOW_BACKEND_LOG_LEVEL = environ.get(
    "SPIFFWORKFLOW_BACKEND_LOG_LEVEL", default="info"
)

# When a user clicks on the `Publish` button, this is the default branch this server merges into.
# I.e., dev server could have `staging` here. Staging server might have `production` here.
SPIFFWORKFLOW_BACKEND_GIT_BRANCH_TO_PUBLISH_TO = environ.get("SPIFFWORKFLOW_BACKEND_GIT_BRANCH_TO_PUBLISH_TO")
SPIFFWORKFLOW_BACKEND_GIT_BRANCH = environ.get("SPIFFWORKFLOW_BACKEND_GIT_BRANCH")
SPIFFWORKFLOW_BACKEND_GIT_CLONE_URL_FOR_PUBLISHING = environ.get("GIT_CLONE_URL")
SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE = environ.get("SPIFFWORKFLOW_BACKEND_GIT_COMMIT_ON_SAVE", default="false") == "true"
SPIFFWORKFLOW_BACKEND_GIT_SSH_PRIVATE_KEY = environ.get("SPIFFWORKFLOW_BACKEND_GIT_SSH_PRIVATE_KEY")
SPIFFWORKFLOW_BACKEND_GIT_USERNAME = environ.get("SPIFFWORKFLOW_BACKEND_GIT_USERNAME")
SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL = environ.get("SPIFFWORKFLOW_BACKEND_GIT_USER_EMAIL")

# Database Configuration
SPIFFWORKFLOW_BACKEND_SPIFF_DATABASE_TYPE = environ.get(
    "SPIFFWORKFLOW_BACKEND_SPIFF_DATABASE_TYPE", default="mysql"
)  # can also be sqlite, postgres
# Overide above with specific sqlalchymy connection string.
SPIFFWORKFLOW_BACKEND_DATABASE_URI = environ.get(
    "SPIFFWORKFLOW_BACKEND_DATABASE_URI", default=None
)
SPIFFWORKFLOW_BACKEND_SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID = environ.get(
    "SPIFFWORKFLOW_BACKEND_SYSTEM_NOTIFICATION_PROCESS_MODEL_MESSAGE_ID",
    default="Message_SystemMessageNotification",
)

SPIFFWORKFLOW_BACKEND_ALLOW_CONFISCATING_LOCK_AFTER_SECONDS = int(
    environ.get("SPIFFWORKFLOW_BACKEND_ALLOW_CONFISCATING_LOCK_AFTER_SECONDS", default="600")
)

SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP = environ.get(
    "SPIFFWORKFLOW_BACKEND_DEFAULT_USER_GROUP", default="everybody"
)
