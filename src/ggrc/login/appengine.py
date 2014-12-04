# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Login handler for using App Engine authentication with Flask-Login

Assumes app.yaml is configured with:

..
  handlers:
    - url: /login
      script: <wsgi_app path>
      login: required

E.g., ``login: required`` must be specified *at least* for the '/login' route.
"""

from google.appengine.api import users
from ggrc.login.common import find_or_create_user_by_email, get_next_url
import flask_login
from flask import url_for, redirect, request, session, flash


def get_user():
  ae_user = users.get_current_user()
  email = ae_user.email()
  nickname = ae_user.nickname()
  user = find_or_create_user_by_email(email, name=nickname)
  return user

def login():
  user = get_user()
  if user.is_enabled:
    flask_login.login_user(user)
    return redirect(get_next_url(request, default_url=url_for('dashboard')))
  else:
    flash(u'That user account is disabled.', 'alert-error')
    return redirect('/')

def logout():
  flask_login.logout_user()
  return redirect(
    users.create_logout_url(
      get_next_url(request, default_url=url_for('index'))))
