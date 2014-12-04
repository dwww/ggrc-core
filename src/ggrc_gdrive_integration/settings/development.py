# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: brad@reciprocitylabs.com
import os

EXTENSIONS = ['ggrc_gdrive_integration']
exports = ["GAPI_KEY", "GAPI_CLIENT_ID", "GAPI_ADMIN_GROUP"]

GAPI_KEY = os.environ.get('GGRC_GAPI_KEY', "AIzaSyAndAzs1E-8brJdESH7YSuvrj3A8Y-MZCg")
GAPI_CLIENT_ID = os.environ.get('GGRC_GAPI_CLIENT_ID', "831270113958.apps.googleusercontent.com")
#Admin group gets writer access to all
GAPI_ADMIN_GROUP = os.environ.get('GGRC_GAPI_ADMIN_GROUP', "ggrc-dev@reciprocitylabs.com")
GAPI_CLIENT_SECRET = os.environ.get('GGRC_GAPI_CLIENT_SECRET', "no-default")
