# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from .mixins import (
    deferred, Noted, Described, Hyperlinked, WithContact, Titled, Slugged,
    )
from .relationship import Relatable
from .object_document import Documentable
from .object_person import Personable
from .object_control import Controllable

class Response(
    Noted, Described, Hyperlinked, WithContact, Titled, Slugged, db.Model):
  __tablename__ = 'responses'
  __mapper_args__ = {
      'polymorphic_on': 'response_type',
      }
  _title_uniqueness = False
  _slug_uniqueness = False

  # Override `Titled.title` to provide default=""
  title = deferred(
      db.Column(db.String, nullable=False, default=""), 'Response')

  VALID_STATES = (u'Assigned', u'Submitted', u'Accepted', u'Rejected')
  VALID_TYPES = (u'documentation', u'interview', u'population sample')
  request_id = deferred(
      db.Column(db.Integer, db.ForeignKey('requests.id'), nullable=False),
      'Response')
  response_type = db.Column(db.Enum(*VALID_TYPES), nullable=False)
  status = deferred(db.Column(db.String, nullable=False),
    'Response')

  population_worksheet_id = deferred(
      db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True),
      'Response')
  population_count = deferred(db.Column(db.Integer, nullable=True),
    'Response')
  sample_worksheet_id = deferred(
      db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True),
      'Response')
  sample_count = deferred(db.Column(db.Integer, nullable=True), 'Response')
  sample_evidence_id = deferred(
      db.Column(db.Integer, db.ForeignKey('documents.id'), nullable=True),
      'Response')

  population_worksheet = db.relationship(
    "Document",
    foreign_keys="PopulationSampleResponse.population_worksheet_id"
    )
  sample_worksheet = db.relationship(
    "Document",
    foreign_keys="PopulationSampleResponse.sample_worksheet_id"
    )
  sample_evidence = db.relationship(
    "Document",
    foreign_keys="PopulationSampleResponse.sample_evidence_id"
    )

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('population_worksheet_document', 'population_worksheet_id'),
        db.Index('sample_evidence_document', 'sample_evidence_id'),
        db.Index('sample_worksheet_document', 'sample_worksheet_id'),
        )

  _publish_attrs = [
      'request',
      'status',
      'response_type',
      ]
  _sanitize_html = [
      'description',
      ]

  def _display_name(self):
    return u'Response with id={0} for Audit "{1}"'.format(
        self.id, self.request.audit.display_name)

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Response, cls).eager_query()
    return query.options(
        orm.joinedload('request'))

class DocumentationResponse(
    Relatable, Documentable, Personable, Controllable, Response):

  __mapper_args__ = {
      'polymorphic_identity': 'documentation'
      }
  _table_plural = 'documentation_responses'

  _publish_attrs = [
      ]
  _sanitize_html = [
      ]


  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(DocumentationResponse, cls).eager_query()
    return query.options()

class InterviewResponse(
    Relatable, Documentable, Personable, Controllable, Response):

  __mapper_args__ = {
      'polymorphic_identity': 'interview'
      }
  _table_plural = 'interview_responses'

  meetings = db.relationship(
    'Meeting',
    backref='response',
    cascade='all, delete-orphan'
    )
  _publish_attrs = [
    'meetings',
      ]
  _sanitize_html = [
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(InterviewResponse, cls).eager_query()
    return query.options(
      orm.subqueryload('meetings'))

class PopulationSampleResponse(
    Relatable, Documentable, Personable, Controllable, Response):

  __mapper_args__ = {
      'polymorphic_identity': 'population sample'
      }
  _table_plural = 'population_sample_responses'

  _publish_attrs = [
      'population_worksheet',
      'population_count',
      'sample_worksheet',
      'sample_count',
      'sample_evidence',
      ]
  _sanitize_html = [
      'population_count',
      'sample_count',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(PopulationSampleResponse, cls).eager_query()
    return query.options(
      orm.joinedload('population_worksheet'),
      orm.joinedload('sample_worksheet'),
      orm.joinedload('sample_evidence'))
