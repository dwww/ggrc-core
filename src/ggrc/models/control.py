# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from .associationproxy import association_proxy
from .category import CategoryBase
from .categorization import Categorizable
from .mixins import (
    deferred, BusinessObject, Hierarchical, Timeboxed,
    )
from .object_document import Documentable
from .object_owner import Ownable
from .object_person import Personable
from .reflection import PublishOnly
from .utils import validate_option


class ControlCategory(CategoryBase):
  __mapper_args__ = {
      'polymorphic_identity': 'ControlCategory'
      }
  _table_plural = 'control_categories'


class ControlAssertion(CategoryBase):
  __mapper_args__ = {
      'polymorphic_identity': 'ControlAssertion'
      }
  _table_plural = 'control_assertions'


class ControlCategorized(Categorizable):
  @declared_attr
  def categorizations(cls):
    return cls.declare_categorizable(
      "ControlCategory", "category", "categories", "categorizations")

  _publish_attrs = [
      'categories',
      PublishOnly('categorizations'),
      ]

  _include_links = [
      #'categories',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(ControlCategorized, cls).eager_query()
    return query.options(
        orm.subqueryload('categorizations').joinedload('category'),
        )


class AssertionCategorized(Categorizable):
  @declared_attr
  def assertations(cls):
    return cls.declare_categorizable(
      "ControlAssertion", "assertion", "assertions", "assertations")

  _publish_attrs = [
      'assertions',
      PublishOnly('assertations'),
      ]

  _include_links = [
      #'assertions',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(AssertionCategorized, cls).eager_query()
    return query.options(
        orm.subqueryload('assertations').joinedload('category'),
        )


class Control(
    Documentable, Personable, ControlCategorized, AssertionCategorized,
    Hierarchical, Timeboxed, Ownable, BusinessObject, db.Model):
  __tablename__ = 'controls'

  company_control = deferred(db.Column(db.Boolean), 'Control')
  directive_id = deferred(
      db.Column(db.Integer, db.ForeignKey('directives.id')), 'Control')
  kind_id = deferred(db.Column(db.Integer), 'Control')
  means_id = deferred(db.Column(db.Integer), 'Control')
  version = deferred(db.Column(db.String), 'Control')
  documentation_description = deferred(db.Column(db.Text), 'Control')
  verify_frequency_id = deferred(db.Column(db.Integer), 'Control')
  fraud_related = deferred(db.Column(db.Boolean), 'Control')
  key_control = deferred(db.Column(db.Boolean), 'Control')
  active = deferred(db.Column(db.Boolean), 'Control')
  principal_assessor_id = deferred(
      db.Column(db.Integer, db.ForeignKey('people.id')), 'Control')
  secondary_assessor_id = deferred(
      db.Column(db.Integer, db.ForeignKey('people.id')), 'Control')

  principal_assessor = db.relationship(
      'Person', uselist=False, foreign_keys='Control.principal_assessor_id')
  secondary_assessor = db.relationship(
      'Person', uselist=False, foreign_keys='Control.secondary_assessor_id')

  kind = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Control.kind_id) == Option.id, '\
                  'Option.role == "control_kind")',
      uselist=False)
  means = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Control.means_id) == Option.id, '\
                  'Option.role == "control_means")',
      uselist=False)
  verify_frequency = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Control.verify_frequency_id) == Option.id, '\
                  'Option.role == "verify_frequency")',
      uselist=False)
  program_controls = db.relationship(
      'ProgramControl', backref='control', cascade='all, delete-orphan')
  programs = association_proxy(
      'program_controls', 'program', 'ProgramControl')
  control_sections = db.relationship(
      'ControlSection', backref='control', cascade='all, delete-orphan')
  sections = association_proxy(
      'control_sections', 'section', 'ControlSection')
  objective_controls = db.relationship(
      'ObjectiveControl', backref='control', cascade='all, delete-orphan')
  objectives = association_proxy(
      'objective_controls', 'objective', 'ObjectiveControl')
  control_controls = db.relationship(
      'ControlControl',
      foreign_keys='ControlControl.control_id',
      backref='control',
      cascade='all, delete-orphan',
      )
  implemented_controls = association_proxy(
      'control_controls', 'implemented_control', 'ControlControl')
  implementing_control_controls = db.relationship(
      'ControlControl',
      foreign_keys='ControlControl.implemented_control_id',
      backref='implemented_control',
      cascade='all, delete-orphan',
      )
  implementing_controls = association_proxy(
      'implementing_control_controls', 'control', 'ControlControl')
  object_controls = db.relationship(
      'ObjectControl', backref='control', cascade='all, delete-orphan')
  directive_controls = db.relationship(
      'DirectiveControl', backref='control', cascade='all, delete-orphan')
  # Not needed for the client at this time
  #mapped_directives = association_proxy(
  #    'directive_controls', 'directive', 'DirectiveControl')

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('ix_controls_principal_assessor', 'principal_assessor_id'),
        db.Index('ix_controls_secondary_assessor', 'secondary_assessor_id'),
        )

  # REST properties
  _publish_attrs = [
      'active',
      'company_control',
      'directive',
      'documentation_description',
      'fraud_related',
      #'implemented_controls',
      #'implementing_controls',
      'key_control',
      'kind',
      'means',
      'sections',
      'objectives',
      'programs',
      'verify_frequency',
      'version',
      'principal_assessor',
      'secondary_assessor',
      PublishOnly('control_controls'),
      PublishOnly('control_sections'),
      PublishOnly('objective_controls'),
      PublishOnly('implementing_control_controls'),
      PublishOnly('directive_controls'),
      PublishOnly('program_controls'),
      'object_controls',
      ]

  _sanitize_html = [
      'documentation_description',
      'version',
      ]

  _include_links = [
      #'control_sections',
      #'objective_controls',
      #'directive_controls',
      #'program_controls',
      #'object_controls',
      ]

  @validates('kind', 'means', 'verify_frequency')
  def validate_control_options(self, key, option):
    desired_role = key if key == 'verify_frequency' else 'control_' + key
    return validate_option(self.__class__.__name__, key, option, desired_role)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(Control, cls).eager_query()
    return cls.eager_inclusions(query, Control._include_links).options(
        orm.joinedload('directive'),
        orm.joinedload('principal_assessor'),
        orm.joinedload('secondary_assessor'),
        orm.subqueryload('control_controls'),
        orm.subqueryload('implementing_control_controls'),
        orm.subqueryload('control_sections'),
        orm.subqueryload('objective_controls'),
        orm.subqueryload('directive_controls').joinedload('directive'),
        orm.subqueryload('program_controls'),
        orm.subqueryload('object_controls'),
        )

  def log_json(self):
    out_json = super(Control, self).log_json()
    # so that event log can refer to deleted directive
    if self.directive:
      out_json["mapped_directive"] = self.directive.display_name
    return out_json
