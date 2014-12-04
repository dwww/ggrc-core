# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from .mixins import Mapping

class ControlSection(Mapping, db.Model):
  __tablename__ = 'control_sections'

  control_id = db.Column(
      db.Integer, db.ForeignKey('controls.id'), nullable=False)
  section_id = db.Column(
      db.Integer, db.ForeignKey('sections.id'), nullable=False)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('control_id', 'section_id'),
        db.Index('ix_control_id', 'control_id'),
        db.Index('ix_section_id', 'section_id'),
        )

  _publish_attrs = [
      'control',
      'section',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ControlSection, cls).eager_query()
    return query.options(
        orm.subqueryload('control'),
        orm.subqueryload('section'))

  def _display_name(self):
    return self.section.display_name + '<->' + self.control.display_name
