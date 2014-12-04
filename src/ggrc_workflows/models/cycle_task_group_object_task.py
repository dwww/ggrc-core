# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


from ggrc import db
from ggrc.models.types import JsonType
from ggrc.models.mixins import (
    Base, Titled, Described, Timeboxed, Stateful, WithContact
    )


class CycleTaskGroupObjectTask(
    WithContact, Stateful, Timeboxed, Described, Titled, Base, db.Model):
  __tablename__ = 'cycle_task_group_object_tasks'
  _title_uniqueness = False

  VALID_STATES = (None, 'InProgress', 'Assigned', 'Finished', 'Declined', 'Verified')

  cycle_id = db.Column(
      db.Integer, db.ForeignKey('cycles.id'), nullable=False)
  cycle_task_group_id = db.Column(
      db.Integer, db.ForeignKey('cycle_task_groups.id'), nullable=False)
  cycle_task_group_object_id = db.Column(
      db.Integer, db.ForeignKey('cycle_task_group_objects.id'), nullable=True)
  task_group_task_id = db.Column(
      db.Integer, db.ForeignKey('task_group_tasks.id'), nullable=False)
  task_group_task = db.relationship(
    "TaskGroupTask",
    foreign_keys="CycleTaskGroupObjectTask.task_group_task_id"
    )
  task_type = db.Column(
      db.String(length=250), nullable=False)
  response_options = db.Column(
      JsonType(), nullable=False, default='[]')
  selected_response_options = db.Column(
      JsonType(), nullable=False, default='[]')

  sort_index = db.Column(
      db.String(length=250), default="", nullable=False)

  _publish_attrs = [
      'cycle',
      'cycle_task_group_object',
      'cycle_task_group',
      'task_group_task',
      'cycle_task_entries',
      'sort_index',
      'task_type',
      'response_options',
      'selected_response_options'
      ]
