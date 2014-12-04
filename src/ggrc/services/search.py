# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import json
from flask import request, current_app
from ggrc.fulltext import get_indexer
from ggrc.utils import DateTimeEncoder, url_for, benchmark

def search():
  terms = request.args.get('q')
  permission_type = request.args.get('__permission_type', 'read')
  permission_model = request.args.get('__permission_model', None)
  if terms is None:
    return current_app.make_response((
      'Query parameter "q" specifying search terms must be provided.',
      400,
      [('Content-Type', 'text/plain')],
      ))

  should_group_by_type = request.args.get('group_by_type', '')
  should_group_by_type = should_group_by_type.lower() == 'true'
  should_just_count = request.args.get('counts_only', '')
  should_just_count = should_just_count.lower() == 'true'

  types = request.args.get('types', '');
  types = [t.strip() for t in types.split(',') if len(t.strip()) > 0]
  if len(types) == 0:
    types = None

  contact_id = request.args.get('contact_id')
  extra_params = request.args.get('extra_params', {})
  extra_columns = request.args.get('extra_columns', {})

  if extra_params:
    # Parse t1:a=b,c=d;t2:e=f into dict {t1:{a:b,c:d},t2:{e:f}}
    extra_params = {k: {kk: vv for kk, vv in
                    map(lambda x: x.split('='), v.split(','))} for k, v in
                    map(lambda x: x.split(':'), extra_params.split(';'))}
  else:
    extra_params = {}

  if extra_columns:
    # Parse a=b,c=d into dict {a:b,c:d}
    extra_columns = {k: v for k, v in map(lambda x: x.split('='), extra_columns.split(','))}
  else:
    extra_columns = {}

  if should_just_count:
    return do_counts(terms, types, contact_id, extra_params, extra_columns)
  if should_group_by_type:
    return group_by_type_search(terms, types, contact_id, extra_params)
  return basic_search(terms, types, permission_type, permission_model, contact_id, extra_params)

def do_counts(terms, types=None, contact_id=None, extra_params={}, extra_columns={}):
  from ggrc.rbac import permissions

  # FIXME: ? This would make the query more efficient, but will also prune
  #   objects the user is allowed to read in other contexts.
  # Remove types that the user can't read
  #types = [type for type in types if permissions.is_allowed_read(type, None)]

  indexer = get_indexer()
  with benchmark("Counts"):
    results = indexer.counts(terms, types=types, contact_id=contact_id,
                             extra_params=extra_params, extra_columns=extra_columns)

  results = [(r[2] if r[2] != "" else r[0], r[1]) for r in results]
  return current_app.make_response((
    json.dumps({ 'results': {
        'selfLink': request.url,
        'counts': dict(results)
        }
      }, cls=DateTimeEncoder),
    200,
    [('Content-Type', 'application/json')],
    ))

def do_search(
    terms, list_for_type, types=None, permission_type='read',
    permission_model=None, contact_id=None, extra_params=None):
  indexer = get_indexer()
  with benchmark("Search"):
    results = indexer.search(
        terms, types=types, permission_type=permission_type,
        permission_model=permission_model, contact_id=contact_id, extra_params=extra_params)
  seen_results = {}

  for result in results:
    id = result.key
    model_type = result.type
    result_pair = (model_type, id)
    if result_pair not in seen_results:
      seen_results[result_pair] = True
      entries_list = list_for_type(model_type)
      entries_list.append({
        'id': id,
        'type': model_type,
        'href': url_for(model_type, id=id),
        })

def make_search_result(entries):
  return current_app.make_response((
    json.dumps({ 'results': {
        'selfLink': request.url,
        'entries': entries,
        }
      }, cls=DateTimeEncoder),
    200,
    [('Content-Type', 'application/json')],
    ))

def basic_search(
    terms, types=None, permission_type='read', permission_model=None,
    contact_id=None, extra_params=None):
  entries = []
  list_for_type = lambda t: entries
  do_search(terms, list_for_type, types, permission_type, permission_model,
            contact_id, extra_params)
  return make_search_result(entries)

def group_by_type_search(terms, types=None, contact_id=None, extra_params={}):
  entries = {}
  list_for_type = \
      lambda t: entries[t] if t in entries else entries.setdefault(t, [])
  do_search(terms, list_for_type, types, contact_id=contact_id,
            extra_params=extra_params)
  return make_search_result(entries)
