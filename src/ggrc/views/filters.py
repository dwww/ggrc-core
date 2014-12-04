# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc.app import app
import ggrc.views

"""Filters for GRC specific Jinja processing
"""

@app.template_filter("with_static_subdomain")
def with_static_subdomain_filter(path):
  import urlparse
  from flask import request
  from ggrc import settings
  if not getattr(settings, 'APP_ENGINE', False) \
      or not getattr(settings, 'USE_APP_ENGINE_ASSETS_SUBDOMAIN', True):
    return path
  scheme, netloc, _, _, _ = urlparse.urlsplit(request.url_root)
  if not netloc.startswith('static-dot-'):
    netloc = 'static-dot-' + netloc
  return urlparse.urlunsplit((scheme, netloc, path, '', ''))

@app.template_filter("viewlink")
def view_link_filter(obj):
  """Create a view link for an object, that navigates
  to its object-view page in the app
  """
  view = getattr(ggrc.views, obj.__class__.__name__, None)
  return view.url_for(obj) if view else None

@app.template_filter("display_class")
def get_display_class_filter(obj):
  """Return the display class for an instance, model, or name.
  Returns one of 'business', 'governance', 'risk', 'programs',
  'objective', 'control', 'people'
  """
  from ggrc.models.mixins import Base
  from ggrc.models import get_model
  if isinstance(obj, type):
    obj = obj.__name__
  elif isinstance(obj, Base):
    obj = obj.__class__.__name__

  if isinstance(obj, (str, unicode)):
    model = get_model(obj)
    obj = model._inflector.model_singular

  if obj in ('Program',):
    return 'program'
  elif obj in ('Control',):
    return 'controls'
  elif obj in ('Objective',):
    return 'objectives'
  elif obj in (
      'Directive', 'Contract', 'Policy', 'Regulation', 'Standard'):
    return 'governance'
  elif obj in (
      'Project', 'Facility', 'Product', 'DataAsset', 'Market',
      'System', 'Process'):
    return 'business'
  elif obj in ('OrgGroup', 'Person'):
    return 'entities'
  elif obj in ('Risk', 'RiskyAttribute'):
    return 'risk'
  else:
    return ''


# Additional generic filters
#

@app.template_filter("underscore")
def underscore_filter(s):
  """Change spaces to underscores and make lowercase
  """
  return "_".join(s.lower().split(' '))

@app.template_filter("nospace")
def nospace_filter(s):
  """Remove spaces
  """
  return "".join(s.split(' '))
