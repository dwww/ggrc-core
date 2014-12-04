# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc import db
from .associationproxy import association_proxy
from .mixins import deferred, BusinessObject
from .object_document import Documentable
from .object_owner import Ownable
from .object_person import Personable
from .object_objective import Objectiveable
from .audit_object import Auditable
from .reflection import PublishOnly

class Objective(
    Auditable, Objectiveable, Documentable, Personable, Ownable, BusinessObject,
    db.Model):
  __tablename__ = 'objectives'

  section_objectives = db.relationship(
      'SectionObjective', backref='objective', cascade='all, delete-orphan')
  sections = association_proxy(
      'section_objectives', 'section', 'SectionObjective')
  objective_controls = db.relationship(
      'ObjectiveControl', backref='objective', cascade='all, delete-orphan')
  controls = association_proxy(
      'objective_controls', 'control', 'ObjectiveControl')
  objective_objects = db.relationship(
      'ObjectObjective', backref='objective', cascade='all, delete-orphan')

  _publish_attrs = [
      PublishOnly('section_objectives'),
      'sections',
      PublishOnly('objective_controls'),
      'controls',
      #'object_objectives',
      'objective_objects',
      ]

  _include_links = [
      #'section_objectives',
      #'objective_controls',
      #'objective_objects',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Objective, cls).eager_query()
    return cls.eager_inclusions(query, Objective._include_links).options(
        orm.subqueryload('section_objectives').joinedload('section'),
        orm.subqueryload('objective_controls'),
        orm.subqueryload('objective_objects'))
