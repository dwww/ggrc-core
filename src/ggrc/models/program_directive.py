# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from .mixins import Mapping

class ProgramDirective(Mapping, db.Model):
  __tablename__ = 'program_directives'

  program_id = db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False)
  directive_id = db.Column(db.Integer, db.ForeignKey('directives.id'), nullable=False)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('program_id', 'directive_id'),
        db.Index('ix_program_id', 'program_id'),
        db.Index('ix_directive_id', 'directive_id'),
        )

  _publish_attrs = [
      'program',
      'directive',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ProgramDirective, cls).eager_query()
    return query.options(
        orm.subqueryload('program'),
        orm.subqueryload('directive'))

  def _display_name(self):
    return self.program.display_name + '<->' + self.directive.display_name

