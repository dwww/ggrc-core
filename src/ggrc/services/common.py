# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com


"""gGRC Collection REST services implementation. Common to all gGRC collection
resources.
"""


import datetime
import ggrc.builder.json
import hashlib
import logging
import time
from blinker import Namespace
from exceptions import TypeError
from flask import url_for, request, current_app, g, has_request_context
from flask.ext.sqlalchemy import Pagination
from flask.views import View
from ggrc import db, utils
from ggrc.utils import as_json, UnicodeSafeJsonWrapper, benchmark
from ggrc.fulltext import get_indexer
from ggrc.fulltext.recordbuilder import fts_record_for
from ggrc.login import get_current_user_id, get_current_user
from ggrc.models.cache import Cache
from ggrc.models.context import Context
from ggrc.models.event import Event
from ggrc.models.revision import Revision
from ggrc.models.exceptions import ValidationError, translate_message
from ggrc.rbac import permissions, context_query_filter
from sqlalchemy import or_, and_
from sqlalchemy.exc import IntegrityError
import sqlalchemy.orm.exc
from werkzeug.exceptions import BadRequest, Forbidden
from wsgiref.handlers import format_date_time
from urllib import urlencode
from .attribute_query import AttributeQueryBuilder
from ggrc.models.background_task import BackgroundTask, create_task

from ggrc import settings
from copy import deepcopy
from sqlalchemy.orm.session import Session
from sqlalchemy import event
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm.attributes import InstrumentedAttribute
from sqlalchemy.orm.properties import RelationshipProperty
from sqlalchemy.ext.associationproxy import AssociationProxy


CACHE_EXPIRY_COLLECTION=60

def get_oauth_credentials():
  from flask import session
  if session.has_key('oauth_credentials'):
    return session['oauth_credentials']
  else:
    return None

def _get_cache_manager():
  from ggrc.cache import CacheManager, MemCache
  cache_manager = CacheManager()
  cache_manager.initialize(MemCache())
  return cache_manager


def get_cache_key(obj, type=None, id=None):
  """Returns a string identifier for the specified object or stub.

  `obj` can be:
    <db.Model> -- declarative model instance
    (type, id) -- tuple
    { 'type': type, 'id': id } -- dict
  """
  if isinstance(obj, tuple):
    type, id = obj
  elif isinstance(obj, dict):
    type = obj.get('type', None)
    id = obj.get('id', None)
  if isinstance(type, (str, unicode)):
    model = ggrc.models.get_model(type)
    assert model is not None, "Invalid model name: {}".format(type)
    type = ggrc.models.get_model(type)._inflector.table_plural
  if not isinstance(obj, (tuple, dict)):
    if type is None:
      type = obj._inflector.table_plural
    if id is None:
      id = obj.id
  return 'collection:{type}:{id}'.format(type=type, id=id)


def get_cache_class(obj):
  return obj.__class__.__name__


def get_related_keys_for_expiration(context, o):
  cls = get_cache_class(o)
  keys = []
  mappings = context.cache_manager.supported_mappings.get(cls, [])
  if len(mappings) > 0:
    for (cls, attr, polymorph) in mappings:
      if polymorph:
        key = get_cache_key(
            None,
            type=getattr(o, '{0}_type'.format(attr)),
            id=getattr(o, '{0}_id'.format(attr)))
        keys.append(key)
      else:
        obj = getattr(o, attr, None)
        if obj:
          if isinstance(obj, list):
            for inner_o in obj:
              key = get_cache_key(inner_o)
              keys.append(key)
          else:
            key = get_cache_key(obj)
            keys.append(key)
  return keys


def update_memcache_before_commit(context, modified_objects, expiry_time):
  """
  Preparing the memccache entries to be updated before DB commit
  Also update the memcache to indicate the status cache operation 'InProgress' waiting for DB commit
  Raises Exception on failures, cannot proceed with DB commit

  Args:
    context: POST/PUT/DELETE HTTP request or import Converter contextual object
    modified_objects:  objects in cache maintained prior to commiting to DB
    expiry_time: Expiry time specified for memcache ADD and DELETE
  Returns:
    None

  """
  if getattr(settings, 'MEMCACHE_MECHANISM', False) is False:
    return

  context.cache_manager = _get_cache_manager()

  if len(modified_objects.new) > 0:
    items_to_add = modified_objects.new.items()
    for o, json_obj in items_to_add:
      cls = get_cache_class(o)
      if context.cache_manager.supported_classes.has_key(cls):
        key = get_cache_key(o)
        context.cache_manager.marked_for_delete.append(key)
        context.cache_manager.marked_for_delete.extend(
            get_related_keys_for_expiration(context, o))

  if len(modified_objects.dirty) > 0:
    items_to_update = modified_objects.dirty.items()
    for o, json_obj in items_to_update:
      cls = get_cache_class(o)
      if context.cache_manager.supported_classes.has_key(cls):
        key = get_cache_key(o)
        context.cache_manager.marked_for_delete.append(key)
        context.cache_manager.marked_for_delete.extend(
            get_related_keys_for_expiration(context, o))

  if len(modified_objects.deleted) > 0:
    items_to_delete=modified_objects.deleted.items()
    for o, json_obj in items_to_delete:
      cls = get_cache_class(o)
      if context.cache_manager.supported_classes.has_key(cls):
        # FIXME: is explicit `id=...` *required* here to avoid querying the
        #   database for a possibly-deleted object?
        key = get_cache_key(o)#, id=json_obj['id'])
        context.cache_manager.marked_for_delete.append(key)
        context.cache_manager.marked_for_delete.extend(
            get_related_keys_for_expiration(context, o))

  status_entries ={}
  for key in context.cache_manager.marked_for_delete:
    build_cache_status(status_entries, 'DeleteOp:' + key, expiry_time, 'InProgress')
  if len(status_entries) > 0:
    current_app.logger.info("CACHE: status entries: " + str(status_entries))
    ret = context.cache_manager.bulk_add(status_entries, expiry_time)
    if ret is not None and len(ret) == 0:
      pass
    else:
      current_app.logger.error('CACHE: Unable to add status for newly created entries in memcache ' + str(ret))


def update_memcache_after_commit(context):
  """
  The memccache entries is updated after DB commit
  Logs error if there are errors in updating entries in cache

  Args:
    context: POST/PUT/DELETE HTTP request or import Converter contextual object
    modified_objects:  objects in cache maintained prior to commiting to DB
  Returns:
    None

  """
  if getattr(settings, 'MEMCACHE_MECHANISM', False) is False:
    return

  if context.cache_manager is None:
    current_app.logger.error("CACHE: Error in initiaizing cache manager")
    return

  cache_manager = context.cache_manager

  # TODO(dan): check for duplicates in marked_for_delete
  if len(cache_manager.marked_for_delete) > 0:
    #current_app.logger.info("CACHE: Bulk Delete: " + str(cache_manager.marked_for_delete))
    delete_result = cache_manager.bulk_delete(cache_manager.marked_for_delete, 0)
    # TODO(dan): handling failure including network errors, currently we log errors
    if delete_result is not True:
      current_app.logger.error("CACHE: Failed to remoe collection from cache")

  status_entries =[]
  for key in cache_manager.marked_for_delete:
    status_entries.append('DeleteOp:' + str(key))
  if len(status_entries) > 0:
    delete_result = cache_manager.bulk_delete(status_entries, 0)
    # TODO(dan): handling failure including network errors, currently we log errors
    if delete_result is not True:
      current_app.logger.error("CACHE: Failed to remove status entries from cache")

  cache_manager.clear_cache()

def build_cache_status(data, key, expiry_timeout, status):
  """
  Build the dictionary for storing operational status of cache

  Args:
    data: dictionary to update
    key: key to dictionary
    expiry_timeout: timeout for expiry cache
    status: Update status entry, e.g.InProgress
  Returns:
    None
  """
  data[key] = {'expiry': expiry_timeout, 'status': status}

def inclusion_filter(obj):
  return permissions.is_allowed_read(obj.__class__.__name__, obj.context_id)

def get_cache(create=False):
  """
  Retrieves the cache from the Flask global object. The create arg
  indicates if a new cache should be created if none exists. If we
  are not in a request context, no cache is created (return None).
  """
  if has_request_context():
    cache = getattr(g, 'cache', None)
    if cache is None and create:
      cache = g.cache = Cache()
    return cache
  else:
    logging.warning("No request context - no cache created")
    return None

def get_modified_objects(session):
  session.flush()
  cache = get_cache()
  if cache:
    return cache.copy()
  else:
    return None

def update_index(session, cache):
  if cache:
    indexer = get_indexer()
    for obj in cache.new:
      indexer.create_record(fts_record_for(obj), commit=False)
    for obj in cache.dirty:
      indexer.update_record(fts_record_for(obj), commit=False)
    for obj in cache.deleted:
      indexer.delete_record(obj.id, obj.__class__.__name__, commit=False)
    session.commit()

def log_event(session, obj=None, current_user_id=None):
  revisions = []
  session.flush()
  if current_user_id is None:
    current_user_id = get_current_user_id()
  cache = get_cache()
  for o, log_json in cache.dirty.items():
    revision = Revision(o, current_user_id, 'modified', log_json)
    revisions.append(revision)
  for o, log_json in cache.deleted.items():
    revision = Revision(o, current_user_id, 'deleted', log_json)
    revisions.append(revision)
  for o, log_json in cache.new.items():
    revision = Revision(o, current_user_id, 'created', log_json)
    revisions.append(revision)
  if obj is None:
    resource_id = 0
    resource_type = None
    action = 'IMPORT'
    context_id = 0
  else:
    resource_id = obj.id
    resource_type = str(obj.__class__.__name__)
    action = request.method
    context_id = obj.context_id
  if revisions:
    event = Event(
      modified_by_id=current_user_id,
      action=action,
      resource_id=resource_id,
      resource_type=resource_type,
      context_id=context_id)
    event.revisions = revisions
    session.add(event)

class ModelView(View):
  DEFAULT_PAGE_SIZE = 20
  MAX_PAGE_SIZE = 100
  pk = 'id'
  pk_type = 'int'

  _model = None

  # Simple accessor properties
  @property
  def request(self):
    return request

  @property
  def model(self):
    return self._model

  @property
  def modified_attr_name(self):
    return 'updated_at'

  @property
  def modified_attr(self):
    """Return the model attribute to be used for Last-Modified header and
    sorting collection elements.
    """
    return getattr(self.model, self.modified_attr_name)

  def modified_at(self, obj):
    return getattr(obj, self.modified_attr_name)

  def _get_type_select_column(self, model):
    mapper = model._sa_class_manager.mapper
    if mapper.polymorphic_on is None:
    #if len(mapper.self_and_descendants) == 1:
      type_column = sqlalchemy.literal(mapper.class_.__name__)
    else:
      # Handle polymorphic types with CASE
      type_column = sqlalchemy.case(
          value=mapper.polymorphic_on,
          whens={
            val: m.class_.__name__
              for val, m in mapper.polymorphic_map.items()
            })
    return type_column

  def _get_type_where_clause(self, model):
    mapper = model._sa_class_manager.mapper
    if mapper.polymorphic_on is None:
      return True
    else:
      mappers = list(mapper.self_and_descendants)
      polymorphic_on_values = list(
          val
          for val, m in mapper.polymorphic_map.items()
          if m in mappers)
      return mapper.polymorphic_on.in_(polymorphic_on_values)

  #def _get_polymorphic_column(self, model):
  #  mapper = model._sa_class_manager.mapper
  #  if len(mapper.self_and_descendants) > 1:
  #    return mapper.polymorphic_on
  #  else:
  #    return sqlalchemy.literal(mapper.class_.__name__)

  def _get_matching_types(self, model):
    mapper = model._sa_class_manager.mapper
    if len(list(mapper.self_and_descendants)) == 1:
      return mapper.class_.__name__
    else:
      # FIXME: Actually needs to use 'self_and_descendants'
      return [m.class_.__name__ for m in mapper.self_and_descendants]

  def get_match_columns(self, model):
    mapper = model._sa_class_manager.mapper
    columns = []
    columns.append(mapper.primary_key[0].label('id'))
    #columns.append(model.id.label('id'))
    columns.append(self._get_type_select_column(model).label('type'))
    columns.append(mapper.c.context_id.label('context_id'))
    columns.append(mapper.c.updated_at.label('updated_at'))
    #columns.append(self._get_polymorphic_column(model))
    return columns

  def get_collection_matches(self, model, filter_by_contexts=True):
    columns = self.get_match_columns(self.model)
    query = db.session.query(*columns).filter(
        self._get_type_where_clause(model))
    return self.filter_query_by_request(
      query, filter_by_contexts=filter_by_contexts)

  def get_resource_match_query(self, model, id):
    columns = self.get_match_columns(model)
    query = db.session.query(*columns).filter(
        and_(
          self._get_type_where_clause(model),
          columns[0] == id))
    return query

  # Default model/DB helpers
  def get_collection(self, filter_by_contexts=True):
    if '__stubs_only' not in request.args and \
        hasattr(self.model, 'eager_query'):
      query = self.model.eager_query()
    else:
      query = db.session.query(self.model)
    return self.filter_query_by_request(
        query, filter_by_contexts=filter_by_contexts)

  def filter_query_by_request(self, query, filter_by_contexts=True):
    joinlist = []
    if request.args:
      querybuilder = AttributeQueryBuilder(self.model)
      filter, joinlist, options = querybuilder.collection_filters(request.args)
      if filter is not None:
        for j in joinlist:
          query = query.join(j)
        query = query.filter(filter)
    if filter_by_contexts:
      contexts = permissions.read_contexts_for(self.model.__name__)
      filter_expr = context_query_filter(self.model.context_id, contexts)
      query = query.filter(filter_expr)
      for j in joinlist:
        j_class = j.property.mapper.class_
        j_contexts = permissions.read_contexts_for(j_class.__name__)
        if j_contexts is not None:
          query = query.filter(
              context_query_filter(j_class.context_id, j_contexts))
    if '__search' in request.args:
      terms = request.args['__search']
      types = self._get_matching_types(self.model)
      indexer = get_indexer()
      models = indexer._get_grouped_types(types)
      search_query = indexer._get_type_query(models, 'read', None)
      search_query = and_(search_query, indexer._get_filter_query(terms))
      search_query = db.session.query(indexer.record_type.key).filter(search_query)
      if '__mywork' in request.args:
        search_query = indexer._add_owner_query(
            search_query, models, get_current_user_id())
      search_subquery = search_query.subquery()
      query = query.filter(self.model.id.in_(search_subquery))
    order_properties = []
    if '__sort' in request.args:
      sort_attrs = request.args['__sort'].split(",")
      sort_desc = request.args.get('__sort_desc', False)
      for sort_attr in sort_attrs:
        attr_desc = sort_desc
        if sort_attr.startswith('-'):
          attr_desc = not sort_desc
          sort_attr = sort_attr[1:]
        order_property = getattr(self.model, sort_attr, None)
        if order_property and hasattr(order_property, 'desc'):
          if attr_desc:
            order_property = order_property.desc()
          order_properties.append(order_property)
        else:
          # Possibly throw an exception instead, if sorting by invalid attribute?
          pass
    order_properties.append(self.modified_attr.desc())
    order_properties.append(self.model.id.desc())
    query = query.order_by(*order_properties)
    if '__limit' in request.args:
      try:
        limit = int(request.args['__limit'])
        query = query.limit(limit)
      except (TypeError, ValueError):
        pass
    query = query.distinct()
    return query

  def get_object(self, id):
    # This could also use `self.pk`
    # .one() is required as long as any .eager_load() adds joins using
    #   'contains_eager()' to the core query, because 'LIMIT 1' breaks up
    #   that JOIN result (e.g. Categorizable)
    try:
      return self.get_collection(filter_by_contexts=False)\
          .filter(self.model.id == id).one()
    except sqlalchemy.orm.exc.NoResultFound:
      return None

  def not_found_message(self):
    return '{0} not found.'.format(self.model._inflector.title_singular)

  def not_found_response(self):
    return current_app.make_response((self.not_found_message(), 404, []))

  def etag(self, last_modified):
    """Generate the etag given a datetime for the last time the resource was
    modified. This isn't as good as an etag generated off of a hash of the
    representation, but, it doesn't require the representation in order to be
    calculated. An alternative would be to keep an etag on the stored
    representation, but this will do for now.

    .. note::

       Using the datetime implies the need for some care - the resolution of
       the time object needs to be sufficient such that you don't end up with
       the same etag due to two updates performed in rapid succession.
    """
    return '"{0}"'.format(hashlib.sha1(str(last_modified)).hexdigest())

  def collection_last_modified(self):
    """Calculate the last time a member of the collection was modified. This
    method relies on the fact that the collection table has an `updated_at` or
    other column with a relevant timestamp; services for models that don't have
    this field **MUST** override this method.
    """
    result = db.session.query(
        self.modified_attr).order_by(self.modified_attr.desc()).first()
    if result is not None:
      return self.modified_at(result)
    return datetime.datetime.now()

  # Routing helpers
  @classmethod
  def endpoint_name(cls):
    return cls.__name__

  @classmethod
  def url_for_preserving_querystring(cls, *args, **kwargs):
    url = cls.url_for(*args, **kwargs)
    # preserve original query string
    idx = request.url.find('?')
    querystring = '' if idx < 0 else '?' + request.url[idx+1:]
    return url + querystring

  @classmethod
  def base_url_for(cls, _memoized_base_url={}):
    if cls not in _memoized_base_url:
      _memoized_base_url[cls] = url_for(cls.endpoint_name())
    return _memoized_base_url[cls]

  @classmethod
  def url_for(cls, *args, **kwargs):
    url = cls.base_url_for()
    if len(args) > 0:
      arg = args[0]
      id = arg if not isinstance(arg, db.Model) else arg.id
      url = url + '/' + str(id)
    if 'id' in kwargs:
      url = url + '/' + str(kwargs['id'])
      del kwargs['id']
    if len(kwargs) > 0:
      url = url + '?' + urlencode(kwargs)
    return url

  @classmethod
  def decorate_view_func(cls, view_func, decorators):
    if not isinstance(decorators, (list, tuple)):
      decorators = (decorators,)
    for decorator in reversed(decorators):
      view_func = decorator(view_func)
    return view_func


# View base class for Views handling
#   - /resources (GET, POST)
#   - /resources/<pk:pk_type> (GET, PUT, POST, DELETE)
class Resource(ModelView):
  """View base class for Views handling.  Will typically be registered with an
  application following a collection style for routes. Collection `GET` and
  `POST` will have a route like `/resources` while collection member
  resource routes will have routes likej `/resources/<pk:pk_type>`.

  To register a Resource subclass FooCollection with a Flask application:

  ..

     FooCollection.add_to(app, '/foos')

  By default will only support the `application/json` content-type.
  """

  signals = Namespace()
  model_posted = signals.signal('Model POSTed',
    """
    Indicates that a model object was received via POST and will be committed
    to the database. The sender in the signal will be the model class of the
    POSTed resource. The following arguments will be sent along with the
    signal:

      :obj: The model instance created from the POSTed JSON.
      :src: The original POSTed JSON dictionary.
      :service: The instance of Resource handling the POST request.
    """,
    )
  model_put = signals.signal('Model PUT',
      """
      Indicates that a model object update was received via PUT and will be
      updated in the database. The sender in the signal will be the model class
      of the PUT resource. The following arguments will be sent along with the
      signal:

        :obj: The model instance updated from the PUT JSON.
        :src: The original PUT JSON dictionary.
        :service: The instance of Resource handling the PUT request.
      """,
      )
  model_deleted = signals.signal('Model DELETEd',
      """
      Indicates that a model object was DELETEd and will be removed from the
      databse. The sender in the signal will be the model class of the DELETEd
      resource. The followin garguments will be sent along with the signal:

        :obj: The model instance removed.
        :service: The instance of Resource handling the DELETE request.
      """,
      )

  def dispatch_request(self, *args, **kwargs):
    method = request.method

    if method in ('POST', 'PUT', 'DELETE')\
        and 'X-Requested-By' not in request.headers:
      raise BadRequest('X-Requested-By header is REQUIRED.')

    if getattr(settings, 'CALENDAR_MECHANISM', False) is True:
      if method in ('POST', 'PUT', 'DELETE'):
        request.oauth_credentials=get_oauth_credentials()

    try:
      if method == 'GET':
        if self.pk in kwargs and kwargs[self.pk] is not None:
          return self.get(*args, **kwargs)
        else:
          return self.collection_get()
      elif method == 'POST':
        if self.pk in kwargs and kwargs[self.pk] is not None:
          return self.post(*args, **kwargs)
        else:
          return self.collection_post()
      elif method == 'PUT':
        return self.put(*args, **kwargs)
      elif method == 'DELETE':
        return self.delete(*args, **kwargs)
      else:
        raise NotImplementedError()
    except (IntegrityError, ValidationError) as v:
      message = translate_message(v)
      current_app.logger.warn(message)
      return ((message, 403, []))
    except Exception as e:
      current_app.logger.exception(e)
      raise

  def post(*args, **kwargs):
    raise NotImplementedError()

  # Default JSON request handlers
  def get(self, id):
    with benchmark("Query for object"):
      obj = self.get_object(id)
    if obj is None:
      return self.not_found_response()
    if 'Accept' in self.request.headers and \
        'application/json' not in self.request.headers['Accept']:
      return current_app.make_response((
        'application/json', 406, [('Content-Type', 'text/plain')]))
    if not permissions.is_allowed_read(self.model.__name__, obj.context_id):
      raise Forbidden()
    if not permissions.is_allowed_read_for(obj):
      raise Forbidden()
    with benchmark("Serialize object"):
      object_for_json = self.object_for_json(obj)

    if 'If-None-Match' in self.request.headers and \
        self.request.headers['If-None-Match'] == self.etag(object_for_json):
      return current_app.make_response((
        '', 304, [('Etag', self.etag(object_for_json))]))
    return self.json_success_response(
      object_for_json, self.modified_at(obj))

  def validate_headers_for_put_or_delete(self, obj):
    missing_headers = []
    if 'If-Match' not in self.request.headers:
      missing_headers.append('If-Match')
    if 'If-Unmodified-Since' not in self.request.headers:
      missing_headers.append('If-Unmodified-Since')
    if missing_headers:
      # rfc 6585 defines a new status code for missing required headers
      return current_app.make_response((
        'If-Match is required.', 428, [('Content-Type', 'text/plain')]))
    if request.headers['If-Match'] != self.etag(self.object_for_json(obj)) or \
        request.headers['If-Unmodified-Since'] != \
          self.http_timestamp(self.modified_at(obj)):
      return current_app.make_response((
          'The resource could not be updated due to a conflict with the '
          'current state on the server. Please resolve the conflict by '
          'refreshing the resource.',
          409,
          [('Content-Type', 'text/plain')]
          ))
    return None

  def json_update(self, obj, src):
    ggrc.builder.json.update(obj, src)

  def put(self, id):
    with benchmark("Query for object"):
      obj = self.get_object(id)
    if obj is None:
      return self.not_found_response()
    if self.request.mimetype != 'application/json':
      return current_app.make_response((
        'Content-Type must be application/json', 415,[]))
    header_error = self.validate_headers_for_put_or_delete(obj)
    if header_error:
      return header_error
    src = UnicodeSafeJsonWrapper(self.request.json)
    root_attribute = self.model._inflector.table_singular
    try:
      src = src[root_attribute]
    except KeyError, e:
      return current_app.make_response((
        'Required attribute "{0}" not found'.format(root_attribute), 400, []))
    if not permissions.is_allowed_update(self.model.__name__, obj.context_id):
      raise Forbidden()
    if not permissions.is_allowed_update_for(obj):
      raise Forbidden()
    new_context = self.get_context_id_from_json(src)
    if new_context != obj.context_id \
        and not permissions.is_allowed_update(self.model.__name__, new_context):
      raise Forbidden()
    with benchmark("Deserialize object"):
      self.json_update(obj, src)
    obj.modified_by_id = get_current_user_id()
    db.session.add(obj)
    self.model_put.send(obj.__class__, obj=obj, src=src, service=self)
    modified_objects = get_modified_objects(db.session)
    log_event(db.session, obj)
    with benchmark("Update memcache before commit for resource collection PUT"):
      update_memcache_before_commit(self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
    with benchmark("Commit"):
      db.session.commit()
    with benchmark("Query for object"):
      obj = self.get_object(id)
    update_index(db.session, modified_objects)
    with benchmark("Update memcache after commit for resource collection PUT"):
      update_memcache_after_commit(self.request)
    with benchmark("Serialize collection"):
      object_for_json = self.object_for_json(obj)
    return self.json_success_response(
        object_for_json, self.modified_at(obj))

  def delete(self, id):
    if 'X-Appengine-Taskname' not in request.headers:
      task = create_task(request.method, request.full_path)
      if getattr(settings, 'APP_ENGINE', False):
        return self.json_success_response(
            self.object_for_json(task, 'background_task'),
            self.modified_at(task))
    else:
      task = BackgroundTask.query.get(request.args.get("task_id"))
    task.start()
    try:
      with benchmark("Query for object"):
        obj = self.get_object(id)
      if obj is None:
        return self.not_found_response()
      header_error = self.validate_headers_for_put_or_delete(obj)
      if header_error:
        return header_error
      if not permissions.is_allowed_delete(self.model.__name__, obj.context_id):
        raise Forbidden()
      if not permissions.is_allowed_delete_for(obj):
        raise Forbidden()
      db.session.delete(obj)
      self.model_deleted.send(obj.__class__, obj=obj, service=self)
      modified_objects = get_modified_objects(db.session)
      log_event(db.session, obj)
      with benchmark("Update memcache before commit for resource collection DELETE"):
        update_memcache_before_commit(self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
      with benchmark("Commit"):
        db.session.commit()
      update_index(db.session, modified_objects)
      with benchmark("Update memcache after commit for resource collection DELETE"):
        update_memcache_after_commit(self.request)
      with benchmark("Query for object"):
        object_for_json = self.object_for_json(obj)
      result = self.json_success_response(
          object_for_json, self.modified_at(obj))
    except:
      import traceback
      task.finish("Failure", traceback.format_exc())
      raise
    task.finish("Success", result)
    return result

  def has_cache(self):
    return getattr(settings, 'MEMCACHE_MECHANISM', False)

  def apply_paging(self, matches_query):
    page_size = min(
        int(request.args.get('__page_size', self.DEFAULT_PAGE_SIZE)),
        self.MAX_PAGE_SIZE)
    if '__page_only' in request.args:
      page_number = int(request.args.get('__page', 0))
      matches = []
      total = matches_query.count()
    else:
      page_number = int(request.args.get('__page', 1))
      matches = matches_query\
          .limit(page_size)\
          .offset((page_number-1)*page_size)\
          .all()
      if page_number == 1 and len(matches) < page_size:
        total = len(matches)
      else:
        total = matches_query.count()
    page = Pagination(
        matches_query, page_number, page_size, total, matches)
    collection_extras = {
        'paging': self.build_page_object_for_json(page)
        }
    return matches, collection_extras

  def get_matched_resources(self, matches):
    cache_objs = {}
    if self.has_cache():
      self.request.cache_manager = _get_cache_manager()
      with benchmark("Query cache for resources"):
        cache_objs = self.get_resources_from_cache(matches)
      database_matches = [m for m in matches if m not in cache_objs]
    else:
      database_matches = matches

    database_objs = {}
    if len(database_matches) > 0:
      with benchmark("Query database for resources"):
        database_objs = self.get_resources_from_database(matches)
      if self.has_cache():
        with benchmark("Add resources to cache"):
          self.add_resources_to_cache(database_objs)
    return cache_objs, database_objs

  def collection_get(self):
    if 'Accept' in self.request.headers and \
        'application/json' not in self.request.headers['Accept']:
      return current_app.make_response((
        'application/json', 406, [('Content-Type', 'text/plain')]))

    matches_query = self.get_collection_matches(self.model)

    matches = None
    extras = None
    if '__page' in request.args or '__page_only' in request.args:
      matches, extras = self.apply_paging(matches_query)
    else:
      matches = matches_query.all()
      extras = {}

    cache_op = None
    if '__stubs_only' in request.args:
      objs = [{
          'id': m[0],
          'type': m[1],
          'href': utils.url_for(m[1], id=m[0]),
          'context_id': m[2]
          } for m in matches]

    else:
      cache_objs, database_objs = self.get_matched_resources(matches)

      objs = {}
      objs.update(cache_objs)
      objs.update(database_objs)

      objs = [objs[m] for m in matches if m in objs]

      with benchmark("Filter resources"):
        objs = filter_resource(objs)

      cache_op = 'Hit' if len(cache_objs) > 0 else 'Miss'

    # Return custom fields specified via `__fields=id,title,description` etc.
    # TODO this can be optimized by filter_resource() not retrieving the other fields to being with
    if '__fields' in request.args:
        custom_fields = request.args['__fields'].split(',')
        objs = [
            {f: o[f] for f in custom_fields if f in o}
            for o in objs]

    with benchmark("Serialize collection"):
      collection = self.build_collection_representation(
          objs, extras=extras)

    if 'If-None-Match' in self.request.headers and \
        self.request.headers['If-None-Match'] == self.etag(collection):
      return current_app.make_response((
        '', 304, [('Etag', self.etag(collection))]))

    return self.json_success_response(
      collection, self.collection_last_modified(), cache_op=cache_op)

  def get_resources_from_cache(self, matches):
    """Get resources from cache for specified matches"""
    resources = {}
    # Skip right to memcache
    memcache_client = self.request.cache_manager.cache_object.memcache_client
    key_matches = {}
    keys = []
    for match in matches:
      key = get_cache_key(None, id=match[0], type=match[1])
      key_matches[key] = match
      keys.append(key)
    while len(keys) > 0:
      slice_keys = keys[:32]
      keys = keys[32:]
      result = memcache_client.get_multi(slice_keys)
      for key in result:
        if 'selfLink' in result[key]:
          resources[key_matches[key]] = result[key]
    return resources

  def add_resources_to_cache(self, match_obj_pairs):
    """Add resources to cache if they are not blocked by DeleteOp entries"""
    # Skip right to memcache
    memcache_client = self.request.cache_manager.cache_object.memcache_client
    key_objs = {}
    key_blockers = {}
    keys = []
    for match, obj in match_obj_pairs.items():
      key = get_cache_key(None, id=match[0], type=match[1])
      delete_op_key = "DeleteOp:{}".format(key)
      keys.append(key)
      key_objs[key] = obj
      key_blockers[key] = delete_op_key
    while len(keys) > 0:
      slice_keys = keys[:32]
      keys = keys[32:]
      blocker_keys = [key_blockers[key] for key in slice_keys]
      result = memcache_client.get_multi(blocker_keys)
      # Reduce `slice_keys` to only unblocked keys
      slice_keys = [
          key for key in slice_keys if key_blockers[key] not in result]
      memcache_client.add_multi(
          {key: key_objs[key] for key in slice_keys})

  def json_create(self, obj, src):
    ggrc.builder.json.create(obj, src)

  def get_context_id_from_json(self, src):
    context = src.get('context', None)
    if context:
      context_id = context.get('id', None)
      try:
        return int(context_id)
      except (ValueError, TypeError):
        return None
    return None

  def handle_create(self, obj, src):
    """Do NOTHING by default"""
    pass

  def collection_post(self):
    if self.request.mimetype != 'application/json':
      return current_app.make_response((
        'Content-Type must be application/json', 415,[]))
    obj = self.model()
    src = UnicodeSafeJsonWrapper(self.request.json)
    root_attribute = self.model._inflector.table_singular
    try:
      src = src[root_attribute]
    except KeyError, e:
      return current_app.make_response((
        'Required attribute "{0}" not found'.format(root_attribute), 400, []))
    if not permissions.is_allowed_create(
        self.model.__name__, self.get_context_id_from_json(src)):
      raise Forbidden()
    if src.get('private') == True and src.get('context') is not None \
        and src['context'].get('id') is not None:
      raise BadRequest(
        'context MUST be "null" when creating a private resource.')
    elif 'context' not in src:
      raise BadRequest('context MUST be specified.')
    else:
      if not permissions.is_allowed_create(
          self.model.__name__, self.get_context_id_from_json(src)):
        raise Forbidden()
    with benchmark("Deserialize object"):
      self.json_create(obj, src)
    self.model_posted.send(obj.__class__, obj=obj, src=src, service=self)
    obj.modified_by_id = get_current_user_id()
    db.session.add(obj)
    modified_objects = get_modified_objects(db.session)
    log_event(db.session, obj)
    with benchmark("Update memcache before commit for resource collection POST"):
      update_memcache_before_commit(self.request, modified_objects, CACHE_EXPIRY_COLLECTION)
    with benchmark("Commit"):
      db.session.commit()
    update_index(db.session, modified_objects)
    with benchmark("Update memcache after commit for resource collection POST"):
      update_memcache_after_commit(self.request)
    with benchmark("Serialize object"):
      object_for_json = self.object_for_json(obj)
    return self.json_success_response(
      object_for_json, self.modified_at(obj), id=obj.id, status=201)

  @classmethod
  def add_to(cls, app, url, model_class=None, decorators=()):
    if model_class:
      service_class = type(model_class.__name__, (cls,), {
        '_model': model_class,
        })
      import ggrc.services
      setattr(ggrc.services, model_class.__name__, service_class)
    else:
      service_class = cls
    view_func = service_class.as_view(service_class.endpoint_name())
    view_func = cls.decorate_view_func(view_func, decorators)
    app.add_url_rule(
        url,
        defaults={cls.pk: None},
        view_func=view_func,
        methods=['GET','POST'])
    app.add_url_rule(
        '{url}/<{type}:{pk}>'.format(url=url, type=cls.pk_type, pk=cls.pk),
        view_func=view_func,
        methods=['GET', 'PUT', 'DELETE'])

  # Response helpers
  @classmethod
  def as_json(cls, obj, **kwargs):
    return as_json(obj, **kwargs)

  def get_properties_to_include(self, inclusions):
    #FIXME This needs to be improved to deal with branching paths... if that's
    #desirable or needed.
    if inclusions is not None:
      if len(inclusions) == 0:
        raise BadRequest(
            'The __include query parameter requires at least one field to be '
            'included.')
      paths = inclusions.split(',')
      inclusions = []
      for p in paths:
        path = p.split('.')
        if len(path) == 1:
          inclusions.append(tuple(path))
        else:
          inclusions.append((path[0], tuple(path[1:])))
    else:
      inclusions = ()
    return inclusions

  def build_page_object_for_json(self, paging):
    def page_args(next_num, per_page):
      # coerce the values to be plain strings, rather than unicode
      ret = dict([(k,unicode(v)) for k,v in request.args.items()])
      ret['__page'] = next_num
      if '__page_size' in ret:
        ret['__page_size'] = per_page
      return ret
    paging_obj = {}
    base_url = self.url_for()
    page_url = lambda params:\
      base_url + '?' + urlencode(utils.encoded_dict(params))
    if paging.has_next:
      paging_obj['next'] = page_url(
          page_args(paging.next_num, paging.per_page))
    if paging.has_prev:
      paging_obj['prev'] = page_url(
          page_args(paging.prev_num, paging.per_page))
    paging_obj['first'] = page_url(page_args(1, paging.per_page))
    paging_obj['last'] = page_url(page_args(paging.pages, paging.per_page))
    paging_obj['count'] = paging.pages
    paging_obj['total'] = paging.total
    return paging_obj

  def get_resources_from_database(self, matches):
    # FIXME: This is cheating -- `matches` should be allowed to be any model
    model = self.model
    ids = { m[0]: m for m in matches }
    query = model.eager_query()
    objs = query.filter(model.id.in_(ids.keys()))
    resources = {}
    includes = self.get_properties_to_include(request.args.get('__include'))
    for obj in objs:
      resources[ids[obj.id]] = ggrc.builder.json.publish(obj, includes)
    ggrc.builder.json.publish_representation(resources)
    return resources

  def build_collection_representation(self, objs, extras=None):
    table_plural = self.model._inflector.table_plural
    collection_name = '{0}_collection'.format(table_plural)
    resource = {
        collection_name: {
          'selfLink': self.url_for_preserving_querystring(),
          table_plural: objs,
          }
        }
    if extras:
      resource[collection_name].update(extras)
    return resource

  def object_for_json(self, obj, model_name=None, properties_to_include=None):
    model_name = model_name or self.model._inflector.table_singular
    json_obj = ggrc.builder.json.publish(
        obj, properties_to_include or [], inclusion_filter)
    ggrc.builder.json.publish_representation(json_obj)
    return { model_name: json_obj }

  def build_resource_representation(self, obj, extras=None):
    table_singular = self.model._inflector.table_singular
    resource = {
        table_singular: obj,
        }
    if extras:
      resource.update(extras)
    return resource

  def http_timestamp(self, timestamp):
    return format_date_time(time.mktime(timestamp.utctimetuple()))

  def json_success_response(
      self, response_object, last_modified, status=200, id=None, cache_op=None):
    headers = [
        ('Last-Modified', self.http_timestamp(last_modified)),
        ('Etag', self.etag(response_object)),
        ('Content-Type', 'application/json'),
        ]
    if id is not None:
      headers.append(('Location', self.url_for(id=id)))
    if cache_op:
      headers.append(('X-GGRC-Cache', cache_op))
    return current_app.make_response(
      (self.as_json(response_object), status, headers))

  def getval(self, src, attr, *args):
    if args:
      return src.get(unicode(attr), *args)
    return src.get(unicode(attr))


class ReadOnlyResource(Resource):
  def dispatch_request(self, *args, **kwargs):
    method = request.method

    if method == 'GET':
      return super(ReadOnlyResource, self).dispatch_request(*args, **kwargs)
    else:
      raise NotImplementedError()


def filter_resource(resource, depth=0, user_permissions=None):
  """
  Returns:
     The subset of resources which are readable based on user_permissions
  """

  if user_permissions is None:
    user_permissions = permissions.permissions_for(get_current_user())

  if type(resource) in (list, tuple):
    filtered = []
    for sub_resource in resource:
      filtered_sub_resource = filter_resource(
          sub_resource, depth=depth+1, user_permissions=user_permissions)
      if filtered_sub_resource is not None:
        filtered.append(filtered_sub_resource)
    return filtered
  elif type(resource) is dict and 'type' in resource:
    # First check current level
    context_id = False
    if 'context' in resource:
      if resource['context'] is None:
        context_id = None
      else:
        context_id = resource['context']['id']
    elif 'context_id' in resource:
      context_id = resource['context_id']
    assert context_id is not False, "No context found for object"

    if not user_permissions.is_allowed_read(resource['type'], context_id):
      return None
    else:
      # Then, filter any typed keys
      for key, value in resource.items():
        if key == 'context':
          # Explicitly allow `context` objects to pass through
          pass
        else:
          # Apply filtering to sub-resources
          if type(value) is dict and 'type' in value:
            resource[key] = filter_resource(
              value, depth=depth+1, user_permissions=user_permissions)
          # elif type(value) in (list,tuple):
          #   resource[key] = filter_resource(
          #     value, depth=depth+1, user_permissions=user_permissions)

      return resource
  else:
    assert False, "Non-object passed to filter_resource"
