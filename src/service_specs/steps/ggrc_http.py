# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import datetime
import json
import ggrc.app
from behave import given, when, then
from iso8601 import parse_date
from sqlalchemy.orm.properties import RelationshipProperty
from time import sleep, time

from tests.ggrc.behave.utils import (
    Example, handle_example_resource, handle_named_example_resource,
    get_inflection, put_resource,
    get_service_endpoint_url, get_service_endpoint_url_for_type,
    get_resource, handle_get_resource_and_name_it,
    handle_post_fails_with_status_and_content,
    handle_post_named_example, post_example,
    handle_get_example_resource, handle_template_text, post_to_endpoint,
    check_for_resource_in_collection,
    )

def get_json_response(context):
  if not hasattr(context, 'json'):
    context.json = context._response.json()
  return context.json

def add_create_permissions(context, rbac_context_id, resource_types):
  if hasattr(context, 'current_user_data'):
    context.current_user_data.setdefault("permissions", {})
    user_perms = context.current_user_data["permissions"]
    permission_type = 'create'
    user_perms.setdefault(permission_type, {})
    for resource_type in resource_types:
      user_perms[permission_type].setdefault(resource_type, {'contexts': []})
      if rbac_context_id not in user_perms[permission_type][resource_type]:
        user_perms[permission_type][resource_type]['contexts'].append(rbac_context_id)
      context.current_user_json = json.dumps(context.current_user_data)

@given('an example "{resource_type}"')
def example_resource(context, resource_type):
  handle_example_resource(context, resource_type)

@given('a new "{resource_type}" named "{example_name}" is created from json')
def named_example_from_json(context, resource_type, example_name):
  text = handle_template_text(context, context.text)
  json_obj = json.loads(text)
  handle_named_example_resource(
      context, resource_type, example_name, **json_obj)

@given('a new "{resource_type}" named "{example_name}"')
def named_example_resource(context, resource_type, example_name, **kwargs):
  handle_named_example_resource(context, resource_type, example_name, **kwargs)

@given('GET of "{typename}" collection')
@when('GET of "{typename}" collection')
def get_collection_for(context, typename):
  do_get_collection_for(context, typename)
  context.collection_type = typename

@given('GET of "{typename}" collection with stubs only')
@when('GET of "{typename}" collection with stubs only')
def get_collection_for_with_stubs_only(context, typename):
  do_get_collection_for(context, typename, stubs_only=True)

@when('GET of "{typename}" collection using id__in for "{resource_name}"')
def get_collection_for_using_id__in(context, typename, resource_name):
  resource = getattr(context, resource_name)
  table_singular = get_inflection(typename, 'table_singular')
  id = resource.value[table_singular]['id']
  handle_get_resource_and_name_it(
      context,
      get_service_endpoint_url_for_type(context, typename) + '?id__in={}'.format(id),
      "collectionresource")

  # Update the individual resource if one is returned
  table_plural = get_inflection(typename, 'table_plural')
  collection_name = table_plural + '_collection'
  if len(context.collectionresource[collection_name][table_plural]) > 0:
    resource = context.collectionresource[collection_name][table_plural][0]
    setattr(context, resource_name, Example(
      typename, { table_singular: resource }))

def do_get_collection_for(context, typename, stubs_only=False):
  handle_get_resource_and_name_it(
      context,
      get_service_endpoint_url_for_type(context, typename) + '?__stubs_only',
      'collectionresource',
      )

@then('"{resource_name}" is in collection')
def check_resource_in_collection(context, resource_name):
  check_for_resource_in_collection(
      context, 'collectionresource', resource_name, True)

@when('"{name}" is POSTed to its collection')
@given('"{name}" is POSTed to its collection')
def post_named_example_to_collection_endpoint(
    context, name, expected_status=201):
  context._response = handle_post_named_example(context, name, expected_status)

@given('"{name}" is in context "{context_id}"')
def set_context_id_for(context, name, context_id):
  example = getattr(context, name)
  example.set('context', {'id': int(context_id)})

@given('HTTP POST of "{name}" to "{url}"')
def simple_post_of_named(context, name, url):
  example = getattr(context, name)
  response = post_example(
      context, example.resource_type, example.value, url)
  assert response.status_code == 200, \
      'Expected status code {0}, received {1}'.format(
          200, response.status_code)
  context._response = response

@given('wait')
@then('wait')
@when('wait')
def do_wait(context):
  t = time()
  if time() - t < 1:
    sleep(1)

@given('HTTP POST to endpoint "{endpoint}"')
def post_to_named_endpoint(context, endpoint):
  text = handle_template_text(context, context.text)
  endpoint_url = get_service_endpoint_url(context, endpoint)
  context._response = post_to_endpoint(context, endpoint_url, text)

@when('the example "{resource_type}" is POSTed to its collection')
def post_example_resource_to_its_collection(context, resource_type):
  post_example_resource(context, resource_type)

def post_example_resource(context, resource_type, url=None):
  context._response = post_example(
      context, resource_type, context.example_resource, url)

@when('GET of "{url}" as "{name}"')
def get_resource_and_name_it(context, url, name):
  handle_get_resource_and_name_it(context, url, name)

@when('GET of the resource "{name}"')
def get_example_resource(context, name, expected_status=200):
  handle_get_example_resource(context, name, expected_status)

@then('a "{status_code}" status code is received')
def validate_status_code(context, status_code):
  assert context._response.status_code == int(status_code), \
      'Expected status code {0}, received {1}'.format(
          status_code, context._response.status_code)

@then('a 201 status code is received')
def validate_status_201(context):
  assert context._response.status_code == 201, \
      'Expected status code 201, received {0}'.format(
          context._response.status_code)

@then('the response has a header "{header}"')
def validate_header_presence(context, header):
  assert header in context._response.headers

@then('the response header "{header}" is "{value}"')
def validate_header_value(context, header, value):
  assert header in context._response.headers
  assert context._response.headers[header] == value

@then('the response has a Location header')
def validate_location_header(context):
  assert 'Location' in context._response.headers

@then('we receive a valid "{resource_type}" in the entity body')
def validate_resource_in_response(context, resource_type):
  assert 'application/json' == context._response.headers['Content-Type']
  assert get_inflection(resource_type, 'table_singular') in get_json_response(context)
  #FIXME more more more

def dates_within_tolerance(original, response):
  floor = datetime.datetime(
      original.year, original.month, original.day, original.hour,
      original.minute, original.second, tzinfo=original.tzinfo)
  ceiling = floor + datetime.timedelta(seconds=1)
  return floor <= response <= ceiling

@then('the received "{resource_type}" matches the one we posted')
def check_resource_equality_for_response(context, resource_type):
  root = get_inflection(resource_type, 'table_singular')
  resp_json = get_json_response(context)[root]
  orig_json = context.example_resource
  for k in orig_json:
    original = context.example_resource[k]
    response = resp_json[unicode(k)]
    # Remove `context_id` from comparison, since it isn't posted
    if isinstance(response, dict) and 'context_id' in response:
      response = dict(response)
      del response['context_id']
    if isinstance(original, datetime.datetime):
      response = parse_date(response)
      assert dates_within_tolerance(original, response), \
          'for {0}: expected {1}, received {2}'.format(
              k, original, response)
      return
    elif isinstance(original, datetime.date):
      response = datetime.datetime.strptime(response, '%Y-%m-%d').date()
    assert original == response, 'for {0}: expected {1}, received {2}'.format(
        k, original, response)

@given('the current user')
def define_current_user_from_pystring(context):
  define_current_user(context, context.text.replace("\n", " ").strip())

@given('current user is "{user_json}"')
def define_current_user(context, user_json):
  import requests
  user_json = handle_template_text(context, user_json)
  if hasattr(context, 'current_user_json'):
    # logout current user
    response = requests.get(
        context.base_url+'/logout',
        headers={
          'Accept': 'text/html',
          'X-Requested-By': 'Reciprocity Behave Tests',
          },
        cookies=getattr(context, 'cookies', {})
        )
    assert response.status_code == 200, 'Failed to logout!!'
    if hasattr(context, 'cookies'):
      delattr(context, 'cookies')
  context.current_user_data = json.loads(user_json.replace('\\"', '"'))
  context.current_user_json = json.dumps(context.current_user_data)

def get_related_resource_types(resource_type, resource_types):
  model = ggrc.models.get_model(resource_type)
  for attr in ggrc.db.inspect(model).attrs:
    if isinstance(attr, RelationshipProperty):
      columns = tuple(attr.local_columns)[0]
      if not (attr.uselist or columns.primary_key):# or columns.nullable):
        # If the resource has subclasses, then it is abstract, so use one of
        #   its subclasses
        related_resource_types = [
            manager.class_.__name__ for manager in
              attr.mapper.class_manager.subclass_managers(True)]
        if len(related_resource_types) == 0:
          related_resource_types = [attr.mapper.class_.__name__]
        for related_resource_type in related_resource_types:
          if related_resource_type not in resource_types:
            resource_types.add(related_resource_type)
            get_related_resource_types(related_resource_type, resource_types)

@given('current user has create permissions on resource types that "{resource_type}" depends on in context "{rbac_context}"')
def add_related_resource_permissions(context, resource_type, rbac_context):
  resource_types = set()
  get_related_resource_types(resource_type, resource_types)
  rbac_context_id = int(getattr(context, rbac_context).get('id'))
  add_create_permissions(context, rbac_context_id, resource_types)

@then('POST of "{resource_name}" to its collection is allowed')
def check_POST_is_allowed(context, resource_name):
  post_named_example_to_collection_endpoint(context, resource_name)

@then('POST of "{resource_name}" to its collection is forbidden')
def check_POST_is_forbidden(context, resource_name):
  post_named_example_to_collection_endpoint(
      context, resource_name, expected_status=403)

@then('POST of "{resource_name}" fails with "{content}"')
def check_post_fails(context, resource_name, content):
  handle_post_fails_with_status_and_content(context, resource_name, expected_status=403, content=content)

@then('GET of "{resource_name}" is allowed')
def check_GET_is_allowed(context, resource_name):
  get_example_resource(context, resource_name)

@then('GET of "{resource_name}" is forbidden')
def check_GET_is_forbidden(context, resource_name):
  get_example_resource(context, resource_name, expected_status=403)

@given('a user with email "{email}" as "{resource_name}"')
def get_or_post_with_email(context, email, resource_name):
  resource = None
  response = get_resource(context, "/api/people?email={0}".format(email))
  if response.status_code == 200:
    collection = response.json()['people_collection']['people']
    if len(collection) > 0:
      resource = collection[0]
  if resource is None:
    response = post_example(context, "Person",
        { "email": email, "context": { "id": None } })
    if response.status_code == 201:
      resource = response.json()['person']
  assert resource is not None, \
    'Failed to find or create a person with email: {email}'.format(email=email)
  setattr(context, resource_name, resource)

def put_example_resource(context, name, expected_status=200):
  example = getattr(context, name)
  url = example.get('selfLink')
  response = put_resource(context, url, example)
  assert response.status_code == expected_status
  if expected_status == 200 or expected_status == 201:
    example = Example(example.resource_type, response.json())
    setattr(context, name, example)

@when('PUT "{resource_name}"')
@then('PUT of "{resource_name}" is allowed')
def check_PUT_is_allowed(context, resource_name):
  put_example_resource(context, resource_name)

@then('PUT of "{resource_name}" is forbidden')
def check_PUT_is_forbidden(context, resource_name):
  put_example_resource(context, resource_name, expected_status=403)

def delete_resource(context, url, resource):
  import requests
  headers={
      'Content-Type': 'application/json',
      'If-Match': resource.response.headers['Etag'],
      'If-Unmodified-Since': resource.response.headers['Last-Modified'],
      'X-Requested-By': 'Reciprocity Behave Tests',
      }
  if hasattr(context, 'current_user_json'):
    headers['X-ggrc-user'] = context.current_user_json
  response = requests.delete(
      context.base_url+url,
      headers=headers,
      cookies=getattr(context, 'cookies', {})
      )
  context.cookies = response.cookies
  return response

def delete_example_resource(context, name, expected_status=200):
  example = getattr(context, name)
  url = example.get('selfLink')
  response = delete_resource(context, url, example)
  assert response.status_code == expected_status

@when('DELETE "{resource_name}"')
@then('DELETE of "{resource_name}" is allowed')
def check_DELETE_is_allowed(context, resource_name):
  delete_example_resource(context, resource_name, expected_status=200)

@then('DELETE of "{resource_name}" is forbidden')
def check_DELETE_is_allowed(context, resource_name):
  delete_example_resource(context, resource_name, expected_status=403)

@then('fail')
def fail(context):
  """Handy force failure so the trace can be retrieved when debugging tests."""
  assert False

@given('link property "{property1}" of "{resource1}" is link property "{property2}" of "{resource2}"')
def copy_link_property(context, property1, resource1, property2, resource2):
  resource1 = getattr(context, resource1)
  resource2 = getattr(context, resource2)
  resource1.set(property1, resource2.get(property2))
