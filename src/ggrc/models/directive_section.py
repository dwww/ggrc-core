# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


from ggrc import db
from .mixins import Mapping


class DirectiveSection(Mapping, db.Model):
  __tablename__ = 'directive_sections'

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('directive_id', 'section_id'),
        #db.Index('ix_directive_id', 'directive_id'),
        #db.Index('ix_section_id', 'section_id'),
        )

  directive_id = db.Column(db.Integer, db.ForeignKey('directives.id'), nullable = False)
  section_id = db.Column(db.Integer, db.ForeignKey('sections.id'), nullable = False)

  _publish_attrs = [
      'directive',
      'section',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(DirectiveSection, cls).eager_query()
    return query.options(
        orm.subqueryload('section'),
        orm.subqueryload('directive'))

  def _display_name(self):
    return self.directive.display_name + '<->' + self.section.display_name
