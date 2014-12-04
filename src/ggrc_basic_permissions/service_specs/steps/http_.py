# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import json
from behave import given
from ggrc.models import Person
from ggrc_basic_permissions.models import Role, UserRole
from tests.ggrc.behave.utils import (
    Example,
    get_service_endpoint_url_for_type,
    get_resource,
    get_inflection,
    handle_named_example_resource,
    post_example,
    )
from tests.ggrc.behave.factories import factory_for
from urllib import urlencode

class Admin(object):
  ORIGINALLY_NO_ATTR = object()

  def __init__(self, context):
    self.context = context

  def __enter__(self):
    self.current_user_data = getattr(
        self.context, "current_user_data", self.ORIGINALLY_NO_ATTR)
    self.current_user_json = getattr(
        self.context, "current_user_json", self.ORIGINALLY_NO_ATTR)
    self.context.execute_steps(u'''
      Given the current user
        """
        { "email": "test.admin@example.com", "name": "GGRC TEST ADMIN",
          "permissions": {
            "__GGRC_ADMIN__": { "__GGRC_ALL__": { "contexts": [0] } }
          }
        }
        """
    ''')

  def __exit__(self, *arg):
    if self.current_user_json != self.ORIGINALLY_NO_ATTR:

      self.context.execute_steps(
          u'Given the current user\n"""\n{0}\n"""'.format(
            self.current_user_json))

@given('a new Role named "{role_name}" is created from json')
def create_role_from_json(context, role_name):
  json_obj = json.loads(context.text)
  handle_named_example_resource(context, Role, role_name, **json_obj)
  
@given('existing Role named "{role_name}"')
def retrieve_role_by_name_to_context(context, role_name):
  role_entry = retrieve_role_by_name(context, role_name)
  role = Example('Role', {'role': role_entry})
  setattr(context, role_name, role)

def retrieve_model_by_properties(
    context, model, properties, require_exactly_one=False):
  url = get_service_endpoint_url_for_type(context, model)
  response = get_resource(context, '{0}?{1}'.format(
    url, urlencode(properties)))
  root = response.json().keys()[0]
  entries = response.json()[root][model.__tablename__]
  if require_exactly_one:
    assert len(entries) == 1
  if len(entries) > 0:
    return entries[0]
  return None

def create_model_with_properties(context, resource_type, properties):
  resource_factory = factory_for(resource_type)
  example = Example(resource_type, resource_factory(**properties))
  response = post_example(context, example.resource_type, example.value)
  assert response.status_code == 201
  return Example(resource_type, response.json())

def retrieve_role_by_name(context, role_name):
  return retrieve_model_by_properties(
      context, Role, {'name': role_name}, require_exactly_one=True)

def retrieve_person_by_email(context, email):
  return retrieve_model_by_properties(context, Person, {'email': email})

def retrieve_role_assignment(context, role_id, person_id):
  return retrieve_model_by_properties(context, UserRole, {
    'role_id': role_id,
    'person_id': person_id,
    })

def create_person_by_email(context, email):
  return create_model_with_properties(context, Person, {
    'email': email, 'context': {'id': None}})

def create_role_assignment(context, role_id, person_id, context_id):
  return create_model_with_properties(
    context, UserRole, {
      'role': {'id': role_id},
      'person': {'id': person_id},
      'context': {'id': context_id},
      })
  
@given('User "{email}" has "{role_name}" role')
def ensure_user_and_role_assignment_in_default(context, email, role_name):
  ensure_user_and_role_assignment(context, email, role_name, None)

@given('User link object for "{email}" as "{object_name}"')
def retrieve_user_link_object(context, email, object_name):
  with Admin(context):
    person = retrieve_person_by_email(context, email)
    assert person is not None and person['id'] is not None
    setattr(context, object_name, {'id': person['id']})

def ensure_user_and_role_assignment(context, email, role_name, context_id):
  with Admin(context):
    role = retrieve_role_by_name(context, role_name)
    role_id = role['id']
    person = retrieve_person_by_email(context, email)
    if person is None:
      person = create_person_by_email(context, email).value['person']
    person_id = person['id']
    role_assignment = retrieve_role_assignment(context, role_id, person_id)
    if role_assignment is None:
      create_role_assignment(context, role_id, person_id, context_id)

@then('the collection is empty')
def assert_collection_empty(context):
  check_empty_collection(context, expect_empty=True)

@then('the collection is not empty')
def assert_collection_not_empty(context):
  check_empty_collection(context, expect_empty=False)

def check_empty_collection(context, expect_empty=True):
  collection = context.collectionresource
  root = collection.keys()[0]
  if '.' in context.collection_type:
    import ggrc_basic_permissions.models
    typename = context.collection_type.split('.')[-1]
    model_class = getattr(ggrc_basic_permissions.models, typename)
  else:
    from ggrc import models
    model_class = getattr(models, context.collection_type, None)
  entry_list = collection[root][model_class._inflector.table_plural]
  if expect_empty:
    assert len(entry_list) == 0, entry_list
  else:
    assert len(entry_list) > 0, entry_list

@then('GET of "{resourcename}" object page is forbidden')
def get_view_object_page_is_forbidden(context, resourcename):
  get_view_object_page(context, resourcename, 403)

@then('GET of "{resourcename}" object page is allowed')
def get_view_object_page_is_allowed(context, resourcename):
  get_view_object_page(context, resourcename, 200)

def get_view_object_page(context, resourcename, expected_status=200):
  headers = {
      'Accept': 'text/html',
      'X-Requested-By': 'Reciprocity Behave Tests',
      }
  resource = getattr(context, resourcename)
  collection_name = get_inflection(resource.resource_type, 'table_singular')
  uri = '/{collection_name}s/{id}'\
      .format(collection_name=collection_name, id=resource.get('id'))
  response = get_resource(context, uri, headers)
  assert response.status_code == expected_status, response
