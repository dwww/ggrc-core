# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: brad@reciprocitylabs.com

from ggrc import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from ggrc.models.mixins import deferred, Base
from ggrc.models.reflection import PublishOnly

class ObjectEvent(Base, db.Model):
  __tablename__ = 'object_events'

  event_id = db.Column(db.String, nullable=False)
  calendar_id = db.Column(db.String, nullable=True)
  eventable_id = db.Column(db.Integer, nullable=False)
  eventable_type = db.Column(db.String, nullable=False)

  @property
  def eventable_attr(self):
    return '{0}_eventable'.format(self.eventable_type)

  @property
  def eventable(self):
    return getattr(self, self.eventable_attr)

  @eventable.setter
  def eventable(self, value):
    self.eventable_id = value.id if value is not None else None
    self.eventable_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.eventable_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        #db.UniqueConstraint('event_id', 'eventable_id', 'eventable_type'),
        )

  _publish_attrs = [
      'event_id',
      'calendar_id',
      'eventable',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ObjectEvent, cls).eager_query()
    return query.options()

  def _display_name(self):
    return self.eventable.display_name + '<-> gdrive event' + self.event_id

class Eventable(object):
  @classmethod
  def late_init_eventable(cls):
    def make_object_events(cls):
      joinstr = 'and_(foreign(ObjectEvent.eventable_id) == {type}.id, '\
                     'foreign(ObjectEvent.eventable_type) == "{type}")'
      joinstr = joinstr.format(type=cls.__name__)
      return db.relationship(
          'ObjectEvent',
          primaryjoin=joinstr,
          backref='{0}_eventable'.format(cls.__name__),
          cascade='all, delete-orphan',
          )
    cls.object_events = make_object_events(cls)

  _publish_attrs = [
      'object_events',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Eventable, cls).eager_query()
    return query.options(
        orm.subqueryload('object_events'))
