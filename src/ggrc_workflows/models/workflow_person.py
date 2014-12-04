# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import backref

from ggrc import db
from ggrc.models.mixins import deferred, Mapping, Timeboxed
from ggrc.models.reflection import PublishOnly


class WorkflowPerson(Mapping, db.Model):
  __tablename__ = 'workflow_people'

  workflow_id = db.Column(
      db.Integer, db.ForeignKey('workflows.id'), nullable=False)
  #workflow = db.relationship(
  #    'Workflow', backref=backref('workflow_people', cascade='all, delete-orphan'))
  person_id = db.Column(
      db.Integer, db.ForeignKey('people.id'), nullable=False)
  person = db.relationship(
      'Person', backref=backref('workflow_people', cascade='all, delete-orphan'))

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('workflow_id', 'person_id'),
        db.Index('ix_workflow_id', 'workflow_id'),
        db.Index('ix_person_id', 'person_id'),
        )

  _publish_attrs = [
      'workflow',
      'person',
      ]
  _sanitize_html = [
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(WorkflowPerson, cls).eager_query()
    return query.options(
        orm.subqueryload('workflow'),
        orm.subqueryload('person'),
        )

  def _display_name(self):
    return self.person.display_name + '<->' + self.workflow.display_name
