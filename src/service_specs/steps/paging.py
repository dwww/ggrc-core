# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from behave import then, when
from tests.ggrc.behave.utils import handle_get_resource_and_name_it

@then('query result has a "{link_name}" page link')
def check_has_page_link(context, link_name):
  check_for_page_link(context, link_name, expected=True)

@then('query result doesn\'t have a "{link_name}" page link')
def check_no_page_link(context, link_name):
  check_for_page_link(context, link_name, expected=False)

def check_for_page_link(context, link_name, expected=True):
  queryresult = context.queryresultcollection
  root = queryresult.keys()[0]
  assert 'paging' in queryresult[root], \
      'Failed to find a "paging" property in the collection!'
  if expected:
    assert link_name in queryresult[root]['paging'], \
        'Failed to find a {} paging link property in the collection!'.format(
            link_name)
    return queryresult[root]['paging'][link_name]
  else:
    assert link_name not in queryresult[root]['paging'], \
        'Unexpectedly found a {} paging link property in the collection!'\
          .format(link_name)
    return None

@when('retrieving query result page "{link_name}"')
def get_named_page_link(context, link_name):
  link = check_for_page_link(context, link_name)
  handle_get_resource_and_name_it(context, link, 'queryresultcollection')
