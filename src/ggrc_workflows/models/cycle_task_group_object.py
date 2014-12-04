# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


from ggrc import db
from ggrc.models.mixins import (
    Base, Titled, Described, Timeboxed, Stateful, WithContact
    )


class CycleTaskGroupObject(
    WithContact, Stateful, Timeboxed, Described, Titled, Base, db.Model):
  __tablename__ = 'cycle_task_group_objects'
  _title_uniqueness = False

  VALID_STATES = (None, u'InProgress', u'Finished', u'Verified', u'Declined')

  cycle_id = db.Column(
      db.Integer, db.ForeignKey('cycles.id'), nullable=False)
  cycle_task_group_id = db.Column(
      db.Integer, db.ForeignKey('cycle_task_groups.id'), nullable=False)
  task_group_object_id = db.Column(
      db.Integer, db.ForeignKey('task_group_objects.id'), nullable=False)
  task_group_object = db.relationship(
    "TaskGroupObject",
    foreign_keys="CycleTaskGroupObject.task_group_object_id"
    )
  cycle_task_group_object_tasks = db.relationship(
      'CycleTaskGroupObjectTask',
      backref='cycle_task_group_object',
      cascade='all, delete-orphan'
      )
  object_id = db.Column(db.Integer, nullable=False)
  object_type = db.Column(db.String, nullable=False)
  next_due_date = db.Column(db.Date)

  _publish_attrs = [
      'cycle',
      'cycle_task_group',
      'task_group_object',
      'cycle_task_group_object_tasks',
      'object',
      'next_due_date',
      ]

  @property
  def object_attr(self):
    return '{0}_object'.format(self.object_type)

  @property
  def object(self):
    return getattr(self, self.object_attr)

  @object.setter
  def object(self, value):
    self.object_id = value.id if value is not None else None
    self.object_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.object_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        #db.UniqueConstraint('cycle_task_group_id', 'object_id', 'object_type'),
        )

  def _display_name(self):
    return \
        self.object.display_name + '<->' + self.cycle_task_group.display_name


class CycleTaskGroupable(object):
  @classmethod
  def late_init_cycle_task_groupable(cls):
    def make_cycle_task_group_objects(cls):
      joinstr = 'and_(foreign(CycleTaskGroupObject.object_id) == {type}.id, '\
                     'foreign(CycleTaskGroupObject.object_type) == "{type}")'
      joinstr = joinstr.format(type=cls.__name__)
      return db.relationship(
          'CycleTaskGroupObject',
          primaryjoin=joinstr,
          backref='{0}_object'.format(cls.__name__),
          #post_update=True
          )
    cls.cycle_task_group_objects = make_cycle_task_group_objects(cls)

  _publish_attrs = [
      #'cycle_task_group_objects',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(CycleTaskGroupable, cls).eager_query()
    return query.options(
        orm.subqueryload('cycle_task_group_objects'),
        )
