# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from .base import *
from ggrc.models import (
    Directive, Policy, Regulation, Contract, Standard, Control, System,
    System, Process, Program, DirectiveControl, ProgramControl
)
from ggrc.models.mixins import BusinessObject
from .base_row import *
from collections import OrderedDict

DIRECTIVE_CLASSES = [Directive, Policy, Regulation, Contract, Standard]

class ControlRowConverter(BaseRowConverter):
  model_class = Control

  def find_by_slug(self, slug):
    from sqlalchemy import orm
    return self.model_class.query.filter_by(slug=slug).options(
        orm.joinedload('directive_controls')).first()

  def setup_object(self):
    self.obj = self.setup_object_by_slug(self.attrs)
    if self.obj.id is not None:
      self.add_warning('slug', "Control already exists and will be updated")

  def reify(self):
    self.handle('slug', SlugColumnHandler)
    self.handle_date('start_date')
    self.handle_date('end_date')
    self.handle_date('created_at', no_import=True)
    self.handle_date('updated_at', no_import=True)
    self.handle_text_or_html('description')

    self.handle_title('title', is_required=True)
    self.handle_raw_attr('url')
    self.handle_raw_attr('reference_url')
    self.handle_text_or_html('notes')
    self.handle_option('kind', role='control_kind')
    self.handle_option('means', role='control_means')
    self.handle_option('verify_frequency')

    self.handle_boolean('key_control', truthy_values=['key', 'key_control',
                        'key control'], no_values=[])
    fraud_truthy = ['fraud', 'fraud_related', 'fraud related']
    fraud_falses = ['not fraud', 'not_fraud','not fraud_related', 'not fraud related']
    self.handle_boolean('fraud_related', truthy_values=fraud_truthy,
      no_values=fraud_falses)
    self.handle_boolean('active', truthy_values = ['active'], no_values = [])

    self.handle('categories', LinkControlCategoriesHandler)
    self.handle('assertions', LinkControlAssertionsHandler)
    self.handle('contact', ContactEmailHandler, person_must_exist=True)
    self.handle('systems', LinkObjectControl, model_class = System)
    self.handle('processes', LinkObjectControl, model_class = Process)
    self.handle('principal_assessor', ContactEmailHandler, person_must_exist=True)
    self.handle('secondary_assessor', ContactEmailHandler, person_must_exist=True)
    self.handle('status', StatusColumnHandler, valid_states=BusinessObject.VALID_STATES)

  def save_object(self, db_session, **options):
    db_session.add(self.obj)

  def after_save(self, db_session, **options):
    super(ControlRowConverter, self).after_save(db_session, **options)
    if options.get('parent_type') in DIRECTIVE_CLASSES:
      directive_id = options.get('parent_id')
      for directive_control in self.obj.directive_controls:
        if directive_control.directive_id == directive_id:
          return
      db_session.add(
          DirectiveControl(directive_id=directive_id, control=self.obj))
    elif options.get('parent_type') == Program:
      program_id = options.get('parent_id')
      for program_control in self.obj.program_controls:
        if program_control.program_id == program_id:
          return
      program = Program.query.get(program_id)
      if program:
          db_session.add(ProgramControl(
              program=program,
              context_id=program.context_id,
              control=self.obj
          ))

class ControlsConverter(BaseConverter):

  metadata_map = OrderedDict([
    ('Type', 'type'),
    ('Directive Code', 'slug')
  ])

  object_map = OrderedDict([
    ('Control Code', 'slug'),
    ('Title', 'title'),
    ('Description', 'description'),
    ('Kind/Nature', 'kind'),
    ('Type/Means', 'means'),
    ('Version', 'version'),
    ('Start Date', 'start_date'),
    ('Stop Date', 'end_date'),
    ('URL', 'url'),
    ('Reference URL', 'reference_url'),
    ('Notes', 'notes'),
    ('Map:Systems', 'systems'),
    ('Map:Processes', 'processes'),
    ('Map:Categories', 'categories'),
    ('Map:Assertions', 'assertions'),
    ('Frequency', 'verify_frequency'),
    ('Map:Person of Contact', 'contact'),
    ('Key Control', 'key_control'),
    ('Active', 'active'),
    ('Fraud Related', 'fraud_related'),
    ('Principal Assessor', 'principal_assessor'),
    ('Secondary Assessor', 'secondary_assessor'),
    ('State', 'status'),
    ('Created', 'created_at'),
    ('Updated' ,'updated_at')
  ])

  row_converter = ControlRowConverter

  def validate_code(self, attrs):
    if not attrs.get('slug'):
      self.errors.append(u'Missing {} Code heading'.format(self.parent_type_string()))
    elif attrs['slug'] != self.parent_object().slug:
      self.errors.append(u'{0} Code must be {1}'.format(
          self.parent_type_string(),
          self.parent_object().slug
      ))

  # Creates the correct metadata_map for the specific directive kind.
  def create_metadata_map(self):
    parent_type = self.options.get('parent_type')
    if parent_type in DIRECTIVE_CLASSES:
      self.metadata_map = OrderedDict( [(k.replace("Directive", self.directive_kind()), v) \
                          if 'Directive' in k else (k, v) for k, v in self.metadata_map.items()] )
    elif parent_type == Program:
      self.metadata_map = OrderedDict( [(k.replace("Directive", "Program"), v) if 'Directive' in k else (k, v) \
          for k, v in self.metadata_map.items()] )

  def validate_metadata(self, attrs):
    self.validate_metadata_type(attrs, "Controls")
    self.validate_code(attrs)

  def parent_object(self):
    parent_type = self.options['parent_type']
    return parent_type.query.get(self.options['parent_id'])

  def parent_type_string(self):
    # must be general enough to handle Directives and Programs
    # while being sure to give a directive's sub-type
    return self.parent_object().__class__.__name__

  def directive_kind(self):
    parent_object = self.parent_object()
    return parent_object.meta_kind

  def do_export_metadata(self):
    yield self.metadata_map.keys()
    yield ['Controls', self.parent_object().slug]
    yield[]
    yield[]
    yield self.object_map.keys()

