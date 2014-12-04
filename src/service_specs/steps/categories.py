# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from behave import given
from tests.ggrc.behave.utils import handle_named_example_resource

@given('a Category resource named "{name}" of type "{category_type}"')
def create_category(context, name, category_type):
  handle_named_example_resource(context, 'Category', name, type=category_type)
