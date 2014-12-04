# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from sqlalchemy.ext.declarative import declared_attr
from .mixins import deferred, Base, Described, Titled, Slugged

class Request(Titled, Slugged, Described, Base, db.Model):
  __tablename__ = 'requests'
  _title_uniqueness = False

  VALID_TYPES = (u'documentation', u'interview')
  VALID_STATES = (u'Draft', u'Requested', u'Responded', u'Amended Request',
    u'Updated Response', u'Accepted')
  requestor_id = db.Column(db.Integer, db.ForeignKey('people.id'))
  requestor = db.relationship('Person', foreign_keys=[requestor_id])
  assignee_id = db.Column(db.Integer, db.ForeignKey('people.id'),
    nullable=False)
  assignee = db.relationship('Person', foreign_keys=[assignee_id])
  request_type = deferred(db.Column(db.Enum(*VALID_TYPES), nullable=False),
    'Request')
  status = deferred(db.Column(db.Enum(*VALID_STATES), nullable=False),
    'Request')
  requested_on = deferred(db.Column(db.Date, nullable=False), 'Request')
  due_on = deferred(db.Column(db.Date, nullable=False), 'Request')
  audit_id = db.Column(db.Integer, db.ForeignKey('audits.id'), nullable=False)
  audit_object_id = db.Column(db.Integer, db.ForeignKey('audit_objects.id'),
    nullable=True)
  gdrive_upload_path = deferred(db.Column(db.String, nullable=True),
    'Request')
  test = deferred(db.Column(db.Text, nullable=True), 'Request')
  notes = deferred(db.Column(db.Text, nullable=True), 'Request')
  responses = db.relationship('Response', backref='request',
    cascade='all, delete-orphan')

  # workaround for title being attached to slug
  @declared_attr
  def title(cls):
    return deferred(db.Column(db.String, nullable=True), cls.__name__)

  _publish_attrs = [
    'assignee',
    'requestor',
    'request_type',
    'gdrive_upload_path',
    'requested_on',
    'due_on',
    'status',
    'audit',
    'audit_object',
    'responses',
    'test',
    'notes',
  ]
  _sanitize_html = [
    'gdrive_upload_path',
    'test',
    'notes',
    'description',
  ]

  def _display_name(self):
    if len(self.description) > 32:
      description_string = self.description[:32] + u'...'
    else:
      description_string = self.description
    return u'Request with id {0} "{1}" for Audit "{2}"'.format(
        self.id,
        description_string,
        self.audit.display_name
    )

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Request, cls).eager_query()
    return query.options(
      orm.joinedload('audit'),
      orm.joinedload('audit_object'),
      orm.subqueryload('responses'))
