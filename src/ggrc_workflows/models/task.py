# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


from ggrc import db
from ggrc.models.mixins import Base, Titled, Slugged, Described, Timeboxed
from ggrc.models.object_owner import Ownable
from ggrc.models.associationproxy import association_proxy
from ggrc.models.reflection import PublishOnly


class Task(Ownable, Timeboxed, Described, Titled, Slugged, Base, db.Model):
  __tablename__ = 'tasks'

  task_group_tasks = db.relationship(
    'TaskGroupTask', backref='task', cascade='all, delete-orphan')
  task_groups = association_proxy(
    'task_group_tasks', 'task_group', 'TaskGroupTask')

  _publish_attrs = [
    'task_group_tasks',
    PublishOnly('task_groups')
    ]
