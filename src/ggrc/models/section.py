# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from sqlalchemy.orm import validates

from ggrc import db
from .associationproxy import association_proxy
from .exceptions import ValidationError
from .mixins import (
    deferred, Hierarchical, Noted, Described, Hyperlinked, WithContact,
    Titled, Slugged,
    )
from .object_document import Documentable
from .object_owner import Ownable
from .object_person import Personable
from .reflection import PublishOnly


class SectionBase(
    Hierarchical, Noted, Described, Hyperlinked, WithContact, Titled, Slugged,
    db.Model):
  _table_plural = 'section_bases'
  __tablename__ = 'sections'
  _title_uniqueness = False

  type = db.Column(db.String)
  directive_id = deferred(
      db.Column(db.Integer, db.ForeignKey('directives.id'), nullable=True),
      'SectionBase')
  na = deferred(db.Column(db.Boolean, default=False, nullable=False),
      'SectionBase')
  notes = deferred(db.Column(db.Text), 'SectionBase')

  control_sections = db.relationship(
      'ControlSection', backref='section', cascade='all, delete-orphan')
  controls = association_proxy(
      'control_sections', 'control', 'ControlSection')
  section_objectives = db.relationship(
      'SectionObjective', backref='section', cascade='all, delete-orphan')
  objectives = association_proxy(
      'section_objectives', 'objective', 'SectionObjective')
  object_sections = db.relationship(
      'ObjectSection', backref='section', cascade='all, delete-orphan')
  directive_sections = db.relationship(
      'DirectiveSection', backref='section', cascade='all, delete-orphan')
  directives = association_proxy(
      'directive_sections', 'directive', 'DirectiveSection')

  __mapper_args__ = {
      'polymorphic_on': type
      }

  _publish_attrs = [
      'directive',
      'na',
      'notes',
      PublishOnly('control_sections'),
      'controls',
      PublishOnly('section_objectives'),
      'objectives',
      PublishOnly('directive_sections'),
      'directives',
      'object_sections',
      ]
  _sanitize_html = [
      'notes',
      ]
  #_update_attrs = [
  #    'directive',
  #    'na',
  #    'notes',
  #    'controls',
  #    'objectives',
  #    'object_sections',
  #    ]

  _include_links = [
      #'control_sections',
      #'section_objectives',
      #'object_sections',
      #'directive_sections',
      ]

  @validates('type')
  def validates_type(self, key, value):
    return self.__class__.__name__

  @classmethod
  def generate_slug_prefix_for(cls, obj):
    from directive import Contract
    if obj.directive and isinstance(obj.directive, Contract):
      return "CLAUSE"
    return super(SectionBase, cls).generate_slug_prefix_for(obj)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(SectionBase, cls).eager_query()
    return cls.eager_inclusions(query, SectionBase._include_links).options(
        orm.joinedload('directive'),
        orm.subqueryload('control_sections'),
        orm.subqueryload('section_objectives'),
        orm.subqueryload('directive_sections'),
        orm.subqueryload('object_sections'))


class Section(Documentable, Personable, Ownable, SectionBase):
  __mapper_args__ = {
      'polymorphic_identity': 'Section'
      }
  _table_plural = 'sections'

  @validates('directive_id')
  def validates_directive_id(self, key, value):
    if self.directive_id:
      return self.directive_id
    raise ValidationError("Directive is required for sections")

  def log_json(self):
    out_json = super(Section, self).log_json()
    # so that event log can refer to deleted directive
    out_json["mapped_directive"] = self.directive.display_name
    return out_json


class Clause(Documentable, Personable, Ownable, SectionBase):
  __mapper_args__ = {
      'polymorphic_identity': 'Clause'
      }
  _table_plural = 'clauses'
