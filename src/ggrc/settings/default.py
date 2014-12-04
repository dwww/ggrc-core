# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

import os

DEBUG = False
TESTING = False

# Flask-SQLAlchemy fix to be less than `wait_time` in /etc/mysql/my.cnf
SQLALCHEMY_POOL_RECYCLE = 120

# Settings in app.py
AUTOBUILD_ASSETS = False
ENABLE_JASMINE = False
DEBUG_ASSETS = False
FULLTEXT_INDEXER = None
USER_PERMISSIONS_PROVIDER = None
EXTENSIONS = []
exports = []

# Deployment-specific variables
COMPANY = "Company, Inc."
COMPANY_LOGO_TEXT = "Company GRC"
COPYRIGHT = u"Confidential. Copyright " + u"\u00A9" # \u00A9 is the (c) symbol

# Construct build number
BUILD_NUMBER = "x"
try:
  import build_number
  BUILD_NUMBER = build_number.BUILD_NUMBER
except (ImportError):
  pass
  
MAJOR_VERSION = "0.9"
MINOR_VERSION = "0"
VERSION = "v" + MAJOR_VERSION + "." + MINOR_VERSION + "." + BUILD_NUMBER

# Google Analytics variables
GOOGLE_ANALYTICS_ID = os.environ.get('GGRC_GOOGLE_ANALYTICS_ID', '')
GOOGLE_ANALYTICS_DOMAIN = os.environ.get('GGRC_GOOGLE_ANALYTICS_DOMAIN', '')

# Initialize from environment if present
SQLALCHEMY_DATABASE_URI = os.environ.get('GGRC_DATABASE_URI', '')
SECRET_KEY = os.environ.get('GGRC_SECRET_KEY', 'Replace-with-something-secret')

MEMCACHE_MECHANISM = True

# AppEngine Email
APPENGINE_EMAIL = os.environ.get('APPENGINE_EMAIL', '')

CALENDAR_MECHANISM = False
