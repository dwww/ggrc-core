# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: vraj@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from .mixins import (
    deferred, Timeboxed, Noted, Described, Hyperlinked, WithContact,
    Titled, Slugged,
    )
from .object_person import Personable
from .context import HasOwnContext
from .reflection import PublishOnly


class Audit(
    Personable, HasOwnContext,
    Timeboxed, Noted, Described, Hyperlinked, WithContact, Titled, Slugged,
    db.Model):
  __tablename__ = 'audits'
  _slug_uniqueness = False

  VALID_STATES = (
      u'Planned', u'In Progress', u'Manager Review',
      u'Ready for External Review', u'Completed'
      )

  report_start_date = deferred(db.Column(db.Date), 'Audit')
  report_end_date = deferred(db.Column(db.Date), 'Audit')
  audit_firm_id = deferred(
      db.Column(db.Integer, db.ForeignKey('org_groups.id')), 'Audit')
  audit_firm = db.relationship('OrgGroup', uselist=False)
  status = deferred(db.Column(db.Enum(*VALID_STATES), nullable=False),
    'Audit')
  gdrive_evidence_folder = deferred(db.Column(db.String), 'Audit')
  program_id = deferred(
      db.Column(db.Integer, db.ForeignKey('programs.id'), nullable=False),
      'Audit')
  requests = db.relationship(
      'Request', backref='audit', cascade='all, delete-orphan')
  audit_objects = db.relationship(
      'AuditObject', backref='audit', cascade='all, delete-orphan')
  object_type = db.Column(db.String(length=250), nullable=False, default='Control')

  _publish_attrs = [
    'report_start_date',
    'report_end_date',
    'audit_firm',
    'status',
    'gdrive_evidence_folder',
    'program',
    'requests',
    'object_type',
    PublishOnly('audit_objects')
    ]

  _sanitize_html = [
    'gdrive_evidence_folder',
    'description',
    ]

  _include_links = [
    #'requests',
    ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Audit, cls).eager_query()
    return query.options(
      orm.joinedload('program'),
      orm.subqueryload('requests'),
      orm.subqueryload('object_people').joinedload('person'))
