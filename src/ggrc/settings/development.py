# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com
import os

DEBUG = True
TESTING = True
HOST = '0.0.0.0'
SQLALCHEMY_DATABASE_URI = 'mysql+mysqldb://root:root@127.0.0.1/ggrcdev?charset=utf8'
FULLTEXT_INDEXER = 'ggrc.fulltext.mysql.MysqlIndexer'
LOGIN_MANAGER = 'ggrc.login.noop'
#SQLALCHEMY_ECHO = True
#SQLALCHEMY_RECORD_QUERIES = True
AUTOBUILD_ASSETS = True
ENABLE_JASMINE = True
#DEBUG_ASSETS = True
USE_APP_ENGINE_ASSETS_SUBDOMAIN = False
MEMCACHE_MECHANISM = False
