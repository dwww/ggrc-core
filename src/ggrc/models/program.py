# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from .associationproxy import association_proxy
from .mixins import deferred, BusinessObject, Timeboxed
from .object_document import Documentable
from .object_objective import Objectiveable
from .object_owner import Ownable
from .object_person import Personable
from .reflection import PublishOnly
from .relationship import Relatable
from .context import HasOwnContext


class Program(
    Documentable, Personable, Objectiveable, Relatable, HasOwnContext,
    Timeboxed, Ownable, BusinessObject, db.Model):
  __tablename__ = 'programs'

  KINDS = [
      'Directive',
      ]

  KINDS_HIDDEN = [
      'Company Controls Policy',
      ]

  private = db.Column(db.Boolean, default=False, nullable=False)
  kind = deferred(db.Column(db.String), 'Program')

  program_controls = db.relationship(
      'ProgramControl', backref='program', cascade='all, delete-orphan')
  controls = association_proxy(
      'program_controls', 'control', 'ProgramControl')
  program_directives = db.relationship(
      'ProgramDirective', backref='program', cascade='all, delete-orphan')
  directives = association_proxy(
      'program_directives', 'directive', 'ProgramDirective')
  audits = db.relationship(
     'Audit', backref='program', cascade='all, delete-orphan')

  _publish_attrs = [
      'kind',
      PublishOnly('program_controls'),
      'controls',
      'program_directives',
      'directives',
      'audits',
      'private',
      ]

  _include_links = [
      #'program_controls',
      #'program_directives',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Program, cls).eager_query()
    return cls.eager_inclusions(query, Program._include_links).options(
        orm.subqueryload('program_directives').joinedload('directive'),
        orm.subqueryload('program_controls'),
        orm.subqueryload('audits'))
