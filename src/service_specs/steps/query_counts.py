# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from behave import given, then


@given('initialized query count for "{endpoint}"')
def initialize_query_count(context, endpoint):
  context.initial_query_count = context.query_count
  context.endpoint = endpoint


@then('query count increment is less than "{max_query_count}"')
def validate_qiuery_count_increment(context, max_query_count):
  max_query_count = int(max_query_count)
  if max_query_count > 0:
    query_count_increment = context.query_count - context.initial_query_count
    assert query_count_increment <= max_query_count, \
        'GET of {0} required {1} queries, which is more than {2}'\
          .format(context.endpoint, query_count_increment, max_query_count)
