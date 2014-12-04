# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from behave import then

@then('"{resource_type}" collection only contains stub entries')
def check_for_stubs_only(context, resource_type):
  collection = context.collectionresource
  root = collection.keys()[0]
  from ggrc import models
  model_class = getattr(models, resource_type)
  for entry in collection[root][model_class._inflector.table_plural]:
    assert len(entry) in [2,3,4]
    assert 'type' in entry and entry['type'] == resource_type
    assert 'href' in entry
    assert 'id' in entry
    assert 'context_id' in entry
