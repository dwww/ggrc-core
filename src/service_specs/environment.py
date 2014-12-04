# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import threading
from ggrc import db
from ggrc.app import app
from ggrc.models import create_db, drop_db
from wsgiref.simple_server import make_server
from ggrc import settings


use_migrations = True 

def before_all(context):
  context.base_url = 'http://localhost:9000'
  create_db(use_migrations)
  app.debug = False
  app.testing = True

  if getattr(settings, 'MEMCACHE_MECHANISM', False) is True:
    from google.appengine.api import memcache
    from google.appengine.ext import testbed
    context.testbed = testbed.Testbed()
    context.testbed.activate()
    context.testbed.init_memcache_stub()

  context.query_count = 0
  def increment_query_count(conn, clauseelement, multiparams, params):
    context.query_count += 1
  from sqlalchemy import event
  event.listen(db.engine, "before_execute", increment_query_count)

  context.server = make_server('', 9000, app)
  context.thread = threading.Thread(target=context.server.serve_forever)
  context.thread.start()

def after_all(context):
  context.server.shutdown()
  context.thread.join()
  db.session.remove()
  drop_db(use_migrations)
  if getattr(settings, 'MEMCACHE_MECHANISM', False) is True:
    from google.appengine.api import memcache
    from google.appengine.ext import testbed
    context.testbed.deactivate()

