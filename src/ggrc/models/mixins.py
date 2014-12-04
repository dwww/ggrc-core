# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

import bleach
from flask import current_app
from ggrc import settings, db
from sqlalchemy import event
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import relationship, validates
from sqlalchemy.orm.session import Session
from uuid import uuid1
from .inflector import ModelInflectorDescriptor
from .reflection import AttributeInfo, PublishOnly
from .computed_property import computed_property

"""Mixins to add common attributes and relationships. Note, all model classes
must also inherit from ``db.Model``. For example:

  ..

     class Market(BusinessObject, db.Model):
       __tablename__ = 'markets'

"""

def deferred(column, classname):
  """Defer column loading for basic properties, such as boolean or string, so
  that they are not loaded on joins. However, Identifiable provides an
  eager_query implementation that will specify undefer in the options so that
  when the resource is loaded itself, rather than through a join, it is
  completely loaded.

  In join tables, this function should not wrap foreign keys nor should it wrap
  type properties for polymorphic relations.
  """
  return db.deferred(column, group=classname+'_complete')

class Identifiable(object):
  """A model with an ``id`` property that is the primary key."""
  id = db.Column(db.Integer, primary_key=True)

  # REST properties
  _publish_attrs = ['id', 'type']
  _update_attrs = []
  _stub_attrs = ['id', 'type']

  _inflector = ModelInflectorDescriptor()

  @computed_property
  def type(self):
    return self.__class__.__name__

  @classmethod
  def eager_query(cls):
    mapper_class = cls._sa_class_manager.mapper.base_mapper.class_
    return db.session.query(cls).options(
        db.Load(mapper_class).undefer_group(mapper_class.__name__+'_complete'),
        )

  @classmethod
  def eager_inclusions(cls, query, include_links):
    from sqlalchemy import orm
    options = []
    for include_link in include_links:
      inclusion_class = getattr(cls, include_link).property.mapper.class_
      options.append(
          orm.subqueryload(include_link)\
              .undefer_group(inclusion_class.__name__ + '_complete'))
    return query.options(*options)

  @declared_attr
  def __table_args__(cls):
    extra_table_args = AttributeInfo.gather_attrs(cls, '_extra_table_args')
    table_args = []
    table_dict = {}
    for table_arg in extra_table_args:
      if callable(table_arg):
        table_arg = table_arg()
      if isinstance(table_arg, (list, tuple, set)):
        if isinstance(table_arg[-1], (dict,)):
          table_dict.update(table_arg[-1])
          table_args.extend(table_arg[:-1])
        else:
          table_args.extend(table_arg)
      elif isinstance(table_arg, (dict,)):
        table_dict.update(table_arg)
      else:
        table_args.append(table_arg)
    if len(table_dict) > 0:
      table_args.append(table_dict)
    return tuple(table_args,)

  # FIXME: This is not the right place, but there is no better common base
  #   class
  def copy_into(self, _other, columns, **kwargs):
    target = _other or type(self)()

    columns = set(columns).union(kwargs.keys())
    for name in columns:
      if name in kwargs:
        value = kwargs[name]
      else:
        value = getattr(self, name)
      setattr(target, name, value)

    return target


def created_at_args():
  """Sqlite doesn't have a server, per se, so the server_* args are useless."""
  return {'default': db.text('current_timestamp'),}

def updated_at_args():
  """Sqlite doesn't have a server, per se, so the server_* args are useless."""
  return {
    'default': db.text('current_timestamp'),
    'onupdate': db.text('current_timestamp'),
    }

class ChangeTracked(object):
  """A model with fields to tracked the last user to modify the model, the
  creation time of the model, and the last time the model was updated.
  """
  # FIXME: change modified_by_id to nullable=False when there is an Account
  # model
  @declared_attr
  def modified_by_id(cls):
    return deferred(db.Column(db.Integer), cls.__name__)

  @declared_attr
  def created_at(cls):
    return deferred(db.Column(
      db.DateTime,
      **created_at_args()), cls.__name__)

  @declared_attr
  def updated_at(cls):
    return deferred(db.Column(
      db.DateTime,
      **updated_at_args()), cls.__name__)

  @declared_attr
  def modified_by(cls):
    return db.relationship(
        'Person',
        primaryjoin='{0}.modified_by_id == Person.id'.format(cls.__name__),
        foreign_keys='{0}.modified_by_id'.format(cls.__name__),
        uselist=False,
        )

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('ix_{}_updated_at'.format(cls.__tablename__), 'updated_at'),
        )

  #TODO Add a transaction id, this will be handy for generating etags
  #and for tracking the changes made to several resources together.
  #transaction_id = db.Column(db.Integer)

  # REST properties
  _publish_attrs = [
      'modified_by',
      'created_at',
      'updated_at',
      ]
  _update_attrs = []


class Titled(object):

  @declared_attr
  def title(cls):
    return deferred(db.Column(db.String, nullable=False), cls.__name__)

  @staticmethod
  def _extra_table_args(cls):
    if getattr(cls, '_title_uniqueness', True):
      return (
          db.UniqueConstraint(
            'title', name='uq_t_{}'.format(cls.__tablename__)),
          )
    return ()

  # REST properties
  _publish_attrs = ['title']
  _fulltext_attrs = ['title']
  _sanitize_html = ['title']


class Described(object):
  @declared_attr
  def description(cls):
    return deferred(db.Column(db.Text), cls.__name__)


  # REST properties
  _publish_attrs = ['description']
  _fulltext_attrs = ['description']
  _sanitize_html = ['description']


class Noted(object):
  @declared_attr
  def notes(cls):
    return deferred(db.Column(db.Text), cls.__name__)

  # REST properties
  _publish_attrs = ['notes']
  _fulltext_attrs = ['notes']
  _sanitize_html = ['notes']


class Hyperlinked(object):
  @declared_attr
  def url(cls):
    return deferred(db.Column(db.String), cls.__name__)

  @declared_attr
  def reference_url(cls):
    return deferred(db.Column(db.String), cls.__name__)

  # REST properties
  _publish_attrs = ['url', 'reference_url']


class Hierarchical(object):
  @declared_attr
  def parent_id(cls):
    return deferred(db.Column(
        db.Integer, db.ForeignKey('{0}.id'.format(cls.__tablename__))),
        cls.__name__)

  @declared_attr
  def children(cls):
    return db.relationship(
        cls.__name__,
        backref=db.backref('parent', remote_side='{0}.id'.format(cls.__name__)),
        )

  # REST properties
  _publish_attrs = [
      'children',
      'parent',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Hierarchical, cls).eager_query()
    return query.options(
        orm.subqueryload('children'),
        #orm.joinedload('parent'),
        )


class Timeboxed(object):
  @declared_attr
  def start_date(cls):
    return deferred(db.Column(db.Date), cls.__name__)

  @declared_attr
  def end_date(cls):
    return deferred(db.Column(db.Date), cls.__name__)

  # REST properties
  _publish_attrs = ['start_date', 'end_date']


class Stateful(object):
  @declared_attr
  def status(cls):
    return deferred(
        db.Column(db.String, default=cls.default_status), cls.__name__)

  _publish_attrs = ['status']

  @classmethod
  def default_status(cls):
    return cls.valid_statuses()[0]

  @classmethod
  def valid_statuses(cls):
    return cls.VALID_STATES

  @validates('status')
  def validate_status(self, key, value):
    if value is None:
      value = self.default_status()
    if value not in self.valid_statuses():
      message = u"Invalid state '{}'".format(value)
      raise ValueError(message)
    return value


class ContextRBAC(object):
  @declared_attr
  def context_id(cls):
    return db.Column(db.Integer, db.ForeignKey('contexts.id'))

  @declared_attr
  def context(cls):
    return db.relationship('Context', uselist=False)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('fk_{}_contexts'.format(cls.__tablename__), 'context_id'),
        )

  _publish_attrs = ['context']

  #@classmethod
  #def eager_query(cls):
    #from sqlalchemy import orm

    #query = super(ContextRBAC, cls).eager_query()
    #return query.options(
        #orm.subqueryload('context'))


class Base(ChangeTracked, ContextRBAC, Identifiable):
  """Several of the models use the same mixins. This class covers that common
  case.
  """

  def log_json(self):
    d = {}
    for column in self.__table__.columns:
      try:
        d[column.name] = getattr(self, column.name)
      except AttributeError:
        pass
    d['display_name'] = self.display_name
    return d

  @computed_property
  def display_name(self):
    try:
      return self._display_name()
    except Exception as e:
      current_app.logger.warn(
          "display_name error in {}".format(type(self)), exc_info=True)
      return ""

  def _display_name(self):
    return getattr(self, "title", None) or getattr(self, "name", "")


class Slugged(Base):
  """Several classes make use of the common mixins and additional are
  "slugged" and have additional fields related to their publishing in the
  system.
  """

  @declared_attr
  def slug(cls):
    return deferred(db.Column(db.String, nullable=False), cls.__name__)

  @staticmethod
  def _extra_table_args(cls):
    if getattr(cls, '_slug_uniqueness', True):
      return (
          db.UniqueConstraint('slug', name='uq_{}'.format(cls.__tablename__)),
          )
    return ()

  # REST properties
  _publish_attrs = ['slug']
  _fulltext_attrs = ['slug']
  _sanitize_html = ['slug']

  @classmethod
  def generate_slug_for(cls, obj):
    id = obj.id if hasattr(obj, 'id') else uuid1()
    obj.slug = "{0}-{1}".format(cls.generate_slug_prefix_for(obj), id)

  @classmethod
  def generate_slug_prefix_for(cls, obj):
    return obj.__class__.__name__.upper()

  @classmethod
  def ensure_slug_before_flush(cls, session, flush_context, instances):
    """Set the slug to a default string so we don't run afoul of the NOT NULL
    constraint.
    """
    for o in session.new:
      if isinstance(o, Slugged) and (o.slug is None or o.slug == ''):
        o.slug = str(uuid1())
        o._replace_slug = True

  @classmethod
  def ensure_slug_after_flush_postexec(cls, session, flush_context):
    """Replace the placeholder slug with a real slug that will be set on the
    next flush/commit.
    """
    for o in session.identity_map.values():
      if isinstance(o, Slugged) and hasattr(o, '_replace_slug'):
        o.generate_slug_for(o)
        delattr(o, '_replace_slug')

event.listen(Session, 'before_flush', Slugged.ensure_slug_before_flush)
event.listen(
  Session, 'after_flush_postexec', Slugged.ensure_slug_after_flush_postexec)


class Mapping(Stateful, Base):
  VALID_STATES = [
      'Draft',
      'Final',
      ]


class WithContact(object):
  @declared_attr
  def contact_id(cls):
    return deferred(
        db.Column(db.Integer, db.ForeignKey('people.id')), cls.__name__)

  @declared_attr
  def contact(cls):
    return db.relationship(
        'Person',
        uselist=False,
        foreign_keys='{}.contact_id'.format(cls.__name__))

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('fk_{}_contact'.format(cls.__tablename__), 'contact_id'),
        )

  _publish_attrs = ['contact']


class BusinessObject(
    Stateful, Noted, Described, Hyperlinked, WithContact, Titled, Slugged):
  VALID_STATES = [
      'Draft',
      'Final',
      'Effective',
      'Ineffective',
      'Launched',
      'Not Launched',
      'In Scope',
      'Not in Scope',
      'Deprecated',
      ]
