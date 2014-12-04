# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


from ggrc import db
from ggrc.models.mixins import (
    Base, Titled, Described, Timeboxed, Stateful, WithContact
    )


class CycleTaskGroup(
    WithContact, Stateful, Timeboxed, Described, Titled, Base, db.Model):
  __tablename__ = 'cycle_task_groups'
  _title_uniqueness = False

  VALID_STATES = (None, u'InProgress', u'Finished', u'Verified', u'Declined')

  cycle_id = db.Column(
      db.Integer, db.ForeignKey('cycles.id'), nullable=False)
  task_group_id = db.Column(
      db.Integer, db.ForeignKey('task_groups.id'), nullable=True)
  cycle_task_group_objects = db.relationship(
      'CycleTaskGroupObject',
      backref='cycle_task_group',
      cascade='all, delete-orphan'
      )
  cycle_task_group_tasks = db.relationship(
      'CycleTaskGroupObjectTask',
      backref='cycle_task_group',
      cascade='all, delete-orphan'
      )
  sort_index = db.Column(
      db.String(length=250), default="", nullable=False)
  next_due_date = db.Column(db.Date)

  _publish_attrs = [
      'cycle',
      'task_group',
      'cycle_task_group_objects',
      'cycle_task_group_tasks',
      'sort_index',
      'next_due_date',
      ]
