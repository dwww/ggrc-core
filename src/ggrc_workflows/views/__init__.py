# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc_workflows import start_recurring_cycles


def do_start_recurring_cycles():
  start_recurring_cycles()
  return 'Ok'


def init_extra_views(app):
  app.add_url_rule(
      "/start_recurring_cycles", "start_recurring_cycles",
      view_func=do_start_recurring_cycles)
