# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc import db
from ggrc.models.mixins import deferred, Base, Titled, Described, Timeboxed, Noted
from ggrc.models.object_document import Documentable

class RiskAssessment(Documentable, Timeboxed, Noted, Described, Titled, Base, db.Model):
  __tablename__ = 'risk_assessments'
  _title_uniqueness = False

  ra_manager_id = deferred(
    db.Column(db.Integer, db.ForeignKey('people.id')), 'RiskAssessment')
  ra_manager = db.relationship(
    'Person', uselist=False, foreign_keys='RiskAssessment.ra_manager_id')

  ra_counsel_id = deferred(
    db.Column(db.Integer, db.ForeignKey('people.id')), 'RiskAssessment')
  ra_counsel = db.relationship(
    'Person', uselist=False, foreign_keys='RiskAssessment.ra_counsel_id')

  program_id = deferred(
    db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False), 'RiskAssessment')
  program = db.relationship(
    'Program',
    backref='risk_assessments',
    uselist=False,
    foreign_keys='RiskAssessment.program_id')

  _fulltext_attrs = [
    ]

  _publish_attrs = [
    'ra_manager',
    'ra_counsel',
    'program',
    ]
