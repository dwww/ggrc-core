# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import datetime
from sqlalchemy.ext.declarative import declared_attr
from ggrc import db
from ggrc.models.mixins import deferred, Base, Described


class Context(Base, db.Model):
  __tablename__ = 'contexts'

  # This block and the 'description' attrs are taken from the Described mixin
  #  which we do not use for Context because indexing Context descriptions
  #  for fulltext search leads to undesirable results
  @declared_attr
  def description(cls):
    return deferred(db.Column(db.Text), cls.__name__)

  name = deferred(db.Column(db.String(128), nullable=True), 'Context')
  related_object_id = deferred(
      db.Column(db.Integer(), nullable=True), 'Context')
  related_object_type = deferred(
      db.Column(db.String(128), nullable=True), 'Context')

  @property
  def related_object_attr(self):
    return '{0}_related_object'.format(self.related_object_type)

  @property
  def related_object(self):
    return getattr(self, self.related_object_attr)

  @related_object.setter
  def related_object(self, value):
    self.related_object_id = value.id if value is not None else None
    self.related_object_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.related_object_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index(
          'ix_context_related_object',
          'related_object_type', 'related_object_id'),
        )

  _publish_attrs = ['name', 'related_object','description',]
  _sanitize_html = ['name','description',]
  _include_links = []


class HasOwnContext(object):
  """Mixin for models which may have their own context
  """

  @declared_attr
  def contexts(cls):
    joinstr = 'and_(foreign(Context.related_object_id) == {type}.id, '\
                   'foreign(Context.related_object_type) == "{type}")'
    joinstr = joinstr.format(type=cls.__name__)
    return db.relationship(
        'Context',
        primaryjoin=joinstr,
        #foreign_keys='Context.related_object_id',
        #cascade='all, delete-orphan',
        backref='{0}_related_object'.format(cls.__name__),
        order_by='Context.id',
        post_update=True)

  def build_object_context(self, context, name=None, description=None):
    if name is None:
      name='{object_type} Context {timestamp}'.format(
        object_type=self.__class__.__name__,
        timestamp=datetime.datetime.now()),
    if description is None:
      description = ''
    new_context = Context(
        name=name,
        description=description,
        related_object=self)
    if isinstance(context, Context):
      new_context.context = context
    else:
      new_context.context_id = context
    return new_context

  def get_or_create_object_context(self, *args, **kwargs):
    if len(self.contexts) == 0:
      new_context = self.build_object_context(*args, **kwargs)
      self.contexts.append(new_context)
    return self.contexts[0]
