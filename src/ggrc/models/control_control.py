# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from .mixins import Mapping

class ControlControl(Mapping, db.Model):
  __tablename__ = 'control_controls'

  control_id = db.Column(
      db.Integer, db.ForeignKey('controls.id'), nullable=False)
  implemented_control_id = db.Column(
      db.Integer, db.ForeignKey('controls.id'), nullable=False)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('control_id', 'implemented_control_id'),
        db.Index('ix_control_id', 'control_id'),
        db.Index('ix_implemented_control_id', 'implemented_control_id'),
        )

  _publish_attrs = [
    'control',
    'implemented_control',
    ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ControlControl, cls).eager_query()
    return query.options(
        orm.subqueryload('control'),
        orm.subqueryload('implemented_control'))

  def _display_name(self):
    return self.implemented_control.display_name + '<->' + self.control.display_name
