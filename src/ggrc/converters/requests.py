# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: silas@reciprocitylabs.com
# Maintained By: silas@reciprocitylabs.com


from .base import *
from ggrc import db
from ggrc.login import get_current_user
from ggrc.models.context import Context
from ggrc.models import Audit, Program, Request, AuditObject
from .base_row import *

from collections import OrderedDict
from datetime import datetime
from ggrc.app import app


class RequestRowConverter(BaseRowConverter):
  model_class = Request

  def find_by_slug(self, slug):
    return self.model_class.query.filter_by(slug=slug).first()

  def setup_object(self):
    self.obj = self.setup_object_by_slug(self.attrs)
    if self.obj.id is not None:
      self.add_warning('slug', "Request already exists and will be updated")

  def reify(self):
    self.handle('slug', SlugColumnHandler)
    self.handle('control_id', ControlHandler, is_needed_later=True)
    self.handle('objective_id', ObjectiveHandler, is_needed_later=True)
    self.handle('request_type', RequestTypeColumnHandler, is_required=True)
    self.handle('status', StatusColumnHandler, valid_states=Request.VALID_STATES, default_value='Draft')
    self.handle_date('requested_on', default_value=datetime.today())
    self.handle_date('due_on', is_required=True)
    self.handle_text_or_html('description')
    self.handle_text_or_html('test')
    self.handle_text_or_html('notes')
    self.handle(
        'assignee', AssigneeHandler, is_required=True,
        person_must_exist=True)

  def save_object(self, db_session, **options):
    audit_id = options.get('audit_id')
    if audit_id:
      audit = Audit.query.get(audit_id)
      self.obj.requestor = get_current_user()
      self.obj.audit = audit
      self.obj.context = audit.context

    if audit and ("Control" == audit.object_type) and getattr(self.obj,'control_id',''):
      ao = AuditObject.query.filter_by(audit_id=audit_id, auditable_id=self.obj.control_id, auditable_type='Control').first()
      if ao:
        self.obj.audit_object=ao
      else:
        context = Context.query.filter_by(related_object_id=audit.id, related_object_type='Audit').first()
        control = Control.query.filter_by(id=self.obj.control_id).first()
        self.obj.audit_object=AuditObject(audit=audit, auditable=control, context=context)
        db_session.add(self.obj.audit_object)

    if audit and ("Objective" == audit.object_type) and getattr(self.obj,'objective_id',''):
      ao = AuditObject.query.filter_by(audit_id=audit_id, auditable_id=self.obj.objective_id, auditable_type='Objective').first()
      if ao:
        self.obj.audit_object=ao
      else:
        context = Context.query.filter_by(related_object_id=audit.id, related_object_type='Audit').first()
        objective = Objective.query.filter_by(id=self.obj.objective_id).first()
        self.obj.audit_object=AuditObject(audit=audit, auditable=objective, context=context)
        db_session.add(self.obj.audit_object)
    db_session.add(self.obj)

class RequestsConverter(BaseConverter):

  metadata_map = OrderedDict([
    ('Type', 'type'),
    ('Program Code', 'slug')
  ])

  object_map = OrderedDict([
    ('Request Code', 'slug'),
    ('Request Type', 'request_type'),
    ('Request Description', 'description'),
    ('Control Code', 'control_id'),
    ('Objective Code', 'objective_id'),
    ('Notes', 'notes'),
    ('Test', 'test'),
    ('Assignee', 'assignee'),
    ('Requested On', 'requested_on'),
    ('Due On', 'due_on'),
    ('Status', 'status'),
  ])

  row_converter = RequestRowConverter

  # code is optional for this object; do the same as in super class
  # but with slug in optional_headers
  def read_headers(self, import_map, row, required_headers=[], optional_headers=[]):
    return super(RequestsConverter, self).read_headers(import_map, row, required_headers, ['slug'] + optional_headers)

  # Overwrite validate functions since they assume a program rather than a directive

  def validate_code(self, attrs):
    true_program_slug = self.program().slug
    given_program_slug = attrs.get('slug')
    if given_program_slug and given_program_slug != true_program_slug:
      self.warnings.append('You have provided {0} as the program code, but this will be imported to program with code {1}.'.format(given_program_slug, true_program_slug))

  def validate_metadata(self, attrs):
    self.validate_metadata_type(attrs, "Requests")
    self.validate_code(attrs)

  def program(self):
    program = Program.query.get(self.options['program_id'])
    return program

  def do_export_metadata(self):
    yield self.metadata_map.keys()
    yield ['Requests', self.program().slug]
    yield[]
    yield[]
    yield self.object_map.keys()
