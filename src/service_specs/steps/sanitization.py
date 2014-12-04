# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from behave import given, then
from tests.ggrc.behave.utils import handle_named_example_resource

@given('"{resource_type}" named "{resource_name}" with sanitized properties '
       '"{properties}"')
def initialize_sanitized_properties(
    context, resource_type, resource_name, properties):
  properties = properties.split(',')
  properties = dict([
      (p.strip(), '<script>foo{}</script>'.format(resource_type))
      for p in properties
      ])
  handle_named_example_resource(
      context, resource_type, resource_name, **properties)

@then('"{resource_type}" "{resource_name}" has sanitized properties "{properties}"')
def check_sanitized_properties(
    context, resource_type, resource_name, properties):
  properties = [p.strip() for p in properties.split(',')]
  resource = getattr(context, resource_name)
  failed = []
  for property in properties:
    value = resource.get(unicode(property))
    if value != u'foo{}'.format(resource_type):
      failed.append('property: {0}, value: {1}'.format(property, value))
  assert len(failed) == 0, '; '.join(failed) + str(resource.value)
