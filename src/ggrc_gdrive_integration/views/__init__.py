# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


import json
from flask import render_template, request, flash, redirect
from ggrc.views import base_context


def gdrive_context():
  ctx = base_context()
  def instance_json():
    return "null"
  ctx["instance_json"] = instance_json
  return ctx


def sandbox():
  """A demo page for GDrive integration models
  """
  return render_template("sandbox/gdrive.haml")


def sandbox_gcal():
  """A demo page for GDrive integration models
  """
  return render_template("sandbox/gcal.haml")


def post_import_requests():
  count = unicode(len(json.loads(request.args.get('ids', '[]'))))
  flash(u'Successfully imported {} request{}'.format(count, 's' if count > 1 else ''), 'notice')
  return_to = unicode(request.args.get('return_to', u'/dashboard'))
  return redirect(return_to)

def init_extra_views(app):
  from ggrc.login import login_required

  app.context_processor(gdrive_context)

  app.add_url_rule(
      "/gdrive_sandbox", "sandbox",
      view_func=login_required(sandbox))
  app.add_url_rule(
      "/gcal_sandbox", "sandbox_gcal",
      view_func=login_required(sandbox_gcal))

  # Since `/audits/post_import_request_hook` is implemented in core, we just
  #   override it here, rather than declare it anew
  app.view_functions['post_import_requests'] =\
      login_required(post_import_requests)
