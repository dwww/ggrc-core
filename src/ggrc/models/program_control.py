# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from .mixins import Mapping

class ProgramControl(Mapping, db.Model):
  __tablename__ = 'program_controls'

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('program_id', 'control_id'),
        db.Index('ix_program_id', 'program_id'),
        db.Index('ix_control_id', 'control_id'),
        )

  program_id = db.Column(
      db.Integer, db.ForeignKey('programs.id'), nullable=False)
  control_id = db.Column(
      db.Integer, db.ForeignKey('controls.id'), nullable=False)

  _publish_attrs = [
      'program',
      'control',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ProgramControl, cls).eager_query()
    return query.options(
        orm.subqueryload('program'),
        orm.subqueryload('control'))

  def _display_name(self):
    return self.control.display_name + '<->' + self.program.display_name
