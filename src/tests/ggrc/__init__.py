# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from flask.ext.testing import TestCase as BaseTestCase
from ggrc import db
from ggrc.app import app
from ggrc.models import create_db, drop_db
from ggrc import settings

use_migrations = False

class TestCase(BaseTestCase):
  def setUp(self):
    create_db(use_migrations, quiet=True)
    if getattr(settings, 'MEMCACHE_MECHANISM', False) is True:
      from google.appengine.api import memcache  
      from google.appengine.ext import testbed 
      self.testbed = testbed.Testbed()
      self.testbed.activate()
      self.testbed.init_memcache_stub()

  def tearDown(self):
    db.session.remove()
    drop_db(use_migrations, quiet=True)
    if getattr(settings, 'MEMCACHE_MECHANISM', False) is True:
      from google.appengine.api import memcache  
      from google.appengine.ext import testbed 
      self.testbed.deactivate()

  def create_app(self):
    app.testing = True
    app.debug = False
    return app
