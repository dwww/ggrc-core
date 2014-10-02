# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from ggrc.models import all_models
from ggrc.models.object_person import ObjectPerson
from ggrc.models.object_owner import ObjectOwner
from ggrc.models.request import Request
from ggrc.models.response import Response
from ggrc_basic_permissions.models import UserRole
from ggrc.rbac import permissions, context_query_filter
from sqlalchemy import \
    event, and_, or_, text, literal, union, alias, case, func, distinct
from sqlalchemy.schema import DDL
from sqlalchemy.ext.declarative import declared_attr
from .sql import SqlIndexer


class MysqlRecordProperty(db.Model):
  __tablename__ = 'fulltext_record_properties'

  key = db.Column(db.Integer, primary_key=True)
  type = db.Column(db.String(64), primary_key=True)
  context_id = db.Column(db.Integer)
  tags = db.Column(db.String)
  property = db.Column(db.String(64), primary_key=True)
  content = db.Column(db.Text)

  @declared_attr
  def __table_args__(cls):
    return (
        # NOTE
        # This is here to prevent Alembic from wanting to drop the index, but
        # the DDL below or a similar Alembic migration should be used to create
        # the index.
        db.Index('{}_text_idx'.format(cls.__tablename__), 'content'),
        # These are real indexes
        db.Index('ix_{}_key'.format(cls.__tablename__), 'key'),
        db.Index('ix_{}_type'.format(cls.__tablename__), 'type'),
        db.Index('ix_{}_tags'.format(cls.__tablename__), 'tags'),
        db.Index('ix_{}_context_id'.format(cls.__tablename__), 'context_id'),
        # Only MyISAM supports fulltext indexes until newer MySQL/MariaDB
        {'mysql_engine': 'myisam'},
        )

event.listen(
    MysqlRecordProperty.__table__,
    'after_create',
    DDL('ALTER TABLE {tablename} ADD FULLTEXT INDEX {tablename}_text_idx '
      '(content)'.format(tablename=MysqlRecordProperty.__tablename__))
    )


class MysqlIndexer(SqlIndexer):
  record_type = MysqlRecordProperty

  def _get_type_query(
      self, model_names, permission_type='read', permission_model=None):

    type_queries = []
    for model_name in model_names:
      type_query = None
      if permission_type == 'read':
        contexts = permissions.read_contexts_for(
            permission_model or model_name)
      elif permission_type == 'create':
        contexts = permissions.create_contexts_for(
            permission_model or model_name)
      elif permission_type == 'update':
        contexts = permissions.update_contexts_for(
            permission_model or model_name)
      elif permission_type == 'delete':
        contexts = permissions.delete_contexts_for(
            permission_model or model_name)

      if permission_model and contexts:
        contexts = set(contexts) & set(
            permissions.read_contexts_for(model_name))

      if contexts is not None:
        type_query = and_(
            MysqlRecordProperty.type == model_name,
            context_query_filter(MysqlRecordProperty.context_id, contexts))
        type_queries.append(type_query)

    return and_(
        MysqlRecordProperty.type.in_(model_names),
        or_(*type_queries))

  def _get_filter_query(self, terms):
    whitelist = MysqlRecordProperty.property.in_(['title', 'name', 'email', 'notes', 'description', 'slug'])
    if not terms:
      return whitelist
    elif terms:
      return and_(whitelist, MysqlRecordProperty.content.contains(terms))

    # FIXME: Temporary (slow) fix for words shorter than MySQL default limit
    # elif len(terms) < 4:
    #   return MysqlRecordProperty.content.contains(terms)
    # else:
    #   return MysqlRecordProperty.content.match(terms)

  def _get_type_select_column(self, model):
    mapper = model._sa_class_manager.mapper
    if mapper.polymorphic_on is None:
      type_column = literal(mapper.class_.__name__)
    else:
      # Handle polymorphic types with CASE
      type_column = case(
          value=mapper.polymorphic_on,
          whens={
            val: m.class_.__name__
              for val, m in mapper.polymorphic_map.items()
            })
    return type_column

  def _types_to_type_models(self, types):
    if types is None:
      return all_models.all_models
    return [m for m in all_models.all_models if m.__name__ in types]

  # filters by "myview" for a given person
  def _add_owner_query(self, query, types=None, contact_id=None):
    '''
    Finds all objects which might appear on a user's Profile or Dashboard
    pages, including:

      Objects mapped via ObjectPerson
      Objects owned via ObjectOwner
      Objects in private contexts via UserRole (e.g. for Private Programs)
      Objects for which the user is the "contact"
      Objects for which the user is the "primary_assessor" or "secondary_assessor"
      Audits for which the user is assigned a Request or Response

    This method only *limits* the result set -- Contexts and Roles will still
    filter out forbidden objects.
    '''
    if not contact_id:
      return query

    type_models = self._types_to_type_models(types)

    model_names = [model.__name__ for model in type_models]

    models = []
    for model in type_models:
      base_model = model._sa_class_manager.mapper.primary_base_mapper.class_
      if base_model not in models:
        models.append(base_model)

    models = [(model, self._get_type_select_column(model)) for model in models]

    type_union_queries = []

    # Objects to which the user is "mapped"
    object_people_query = db.session.query(
        ObjectPerson.personable_id.label('id'),
        ObjectPerson.personable_type.label('type'),
        literal(None).label('context_id')
      ).filter(
          and_(
            ObjectPerson.person_id == contact_id,
            ObjectPerson.personable_type.in_(model_names)
          )
      )
    type_union_queries.append(object_people_query)

    # Objects for which the user is an "owner"
    object_owners_query = db.session.query(
        ObjectOwner.ownable_id.label('id'),
        ObjectOwner.ownable_type.label('type'),
        literal(None).label('context_id')
      ).filter(
          and_(
            ObjectOwner.person_id == contact_id,
            ObjectOwner.ownable_type.in_(model_names),
          )
      )
    type_union_queries.append(object_owners_query)

    # FIXME The following line crashes if the Workflow extension is not enabled
    for model in [all_models.Program, all_models.Audit, all_models.Workflow]:
      context_query = db.session.query(
          model.id.label('id'),
          literal(model.__name__).label('type'),
          literal(None).label('context_id'),
        ).join(
            UserRole,
            and_(
              UserRole.context_id == model.context_id,
              UserRole.person_id == contact_id,
            )
        )
      type_union_queries.append(context_query)

    for model, type_column in models:
      # Audits where the user is assigned a Request or a Response
      if model is all_models.Audit:
        model_type_query = db.session.query(
            Request.audit_id.label('id'),
            type_column.label('type'),
            literal(None).label('context_id')
          ).join(Response).filter(
              or_(
                Request.assignee_id == contact_id,
                Response.contact_id == contact_id
              )
          ).distinct()
        type_union_queries.append(model_type_query)

      # Objects for which the user is the "contact"
      if hasattr(model, 'contact_id'):
        model_type_query = db.session.query(
            model.id.label('id'),
            type_column.label('type'),
            literal(None).label('context_id')
          ).filter(
              model.contact_id == contact_id
          ).distinct()
        type_union_queries.append(model_type_query)

      if model is all_models.Control:
        # Control also has `principal_assessor` and `secondary_assessor`
        assessor_queries = []
        if hasattr(model, 'principal_assessor_id'):
          assessor_queries.append(or_(model.principal_assessor_id == contact_id))
        if hasattr(model, 'secondary_assessor_id'):
          assessor_queries.append(or_(model.secondary_assessor_id == contact_id))

        model_type_query = db.session.query(
            model.id.label('id'),
            type_column.label('type'),
            literal(None).label('context_id')
          ).filter(
              or_(*assessor_queries)
          ).distinct()
        type_union_queries.append(model_type_query)

    # Construct and JOIN to the UNIONed result set
    type_union_query = alias(union(*type_union_queries))
    query = query.join(
        type_union_query,
        and_(
          type_union_query.c.id == MysqlRecordProperty.key,
          type_union_query.c.type == MysqlRecordProperty.type),
      )

    return query

  def _add_extra_params_query(self, query, type, extra_param):
    if not extra_param:
      return query

    models = [m for m in all_models.all_models if m.__name__ == type]

    if len(models) == 0:
      return query
    model = models[0]

    return query.filter(self.record_type.key.in_(
        db.session.query(
            model.id.label('id')
        ).filter_by(**extra_param)
    ))

  def _get_grouped_types(self, types, extra_params=None):
    model_names = [model.__name__ for model in all_models.all_models]
    if types is not None:
      model_names = [m for m in model_names if m in types]

    if extra_params is not None:
      model_names = [m for m in model_names if m not in extra_params]
    return model_names

  def search(
      self, terms, types=None, permission_type='read', permission_model=None, contact_id=None, extra_params={}):
    model_names = self._get_grouped_types(types, extra_params)
    query = db.session.query(
        self.record_type.key, self.record_type.type,
        self.record_type.property, self.record_type.content)
    query = query.filter(
        self._get_type_query(model_names, permission_type, permission_model))
    query = query.filter(self._get_filter_query(terms))
    query = self._add_owner_query(query, types, contact_id)

    model_names = [model.__name__ for model in all_models.all_models]
    if types is not None:
      model_names = [m for m in model_names if m in types]

    unions = []
    # Add extra_params and extra_colums:
    for k, v in extra_params.iteritems():
      if k not in model_names:
        continue
      q = db.session.query(
          self.record_type.key, self.record_type.type,
          self.record_type.property, self.record_type.content)
      q = q.filter(
          self._get_type_query([k], permission_type, permission_model))
      q = q.filter(self._get_filter_query(terms))
      q = self._add_owner_query(q, [k], contact_id)
      q = self._add_extra_params_query(q, k, v)
      unions.append(q)
    # Sort by title:
    # FIXME: This only orders by `title` if title was the matching property
    query = query.union(*unions)
    query = query.order_by(case(
      [(self.record_type.property == "title", self.record_type.content)],
      else_=literal("ZZZZZ")))
    return query

  def counts(self, terms, group_by_type=True, types=None, contact_id=None, extra_params={}, extra_columns={}):
    model_names = self._get_grouped_types(types, extra_params)
    query = db.session.query(
        self.record_type.type, func.count(distinct(self.record_type.key)), literal(""))
    query = query.filter(self._get_type_query(model_names))
    query = query.filter(self._get_filter_query(terms))
    query = self._add_owner_query(query, types, contact_id)
    query = query.group_by(self.record_type.type)
    all_extra_columns = dict(extra_columns.items() +
        [(p, p) for p in extra_params if p not in extra_columns]
    )
    if not all_extra_columns:
      return query.all()

    # Add extra_params and extra_colums:
    for k, v in all_extra_columns.iteritems():
      q = db.session.query(
          self.record_type.type, func.count(distinct(self.record_type.key)), literal(k))
      q = q.filter(self._get_type_query([v]))
      q = q.filter(self._get_filter_query(terms))
      q = self._add_owner_query(q, [v], contact_id)
      q = self._add_extra_params_query(q, v, extra_params.get(k, None))
      q = q.group_by(self.record_type.type)
      query = query.union(q)
    return query.all()

Indexer = MysqlIndexer
