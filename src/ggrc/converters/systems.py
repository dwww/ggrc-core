# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from .base import *
from ggrc.models.all_models import SystemOrProcess, System, OrgGroup, Program, Relationship, Vendor
from ggrc.models.mixins import BusinessObject
from .base_row import *
from collections import OrderedDict

class SystemRowConverter(BaseRowConverter):
  model_class = System

  def find_by_slug(self, slug):
    # must search systems and processes for this case
    return SystemOrProcess.query.filter_by(slug=slug).first()

  def setup_object(self):
    self.obj = self.setup_object_by_slug(self.attrs)
    if self.obj.id is None:
      self.obj.infrastructure = self.obj.infrastructure or False
      self.obj.is_biz_process = self.importer.options.get('is_biz_process') or False
    else:
      if self.obj.is_biz_process and not self.importer.options.get('is_biz_process'):
        self.add_error('slug', "Code is already used for a Process")
      elif (not self.obj.is_biz_process) and self.importer.options.get('is_biz_process'):
        self.add_error('slug', "Code is already used for a System")
      else:
        sys_type = "Process" if self.importer.options.get('is_biz_process') else "System"
        self.add_warning('slug', "{} already exists and will be updated".format(sys_type))

  def reify(self):
    self.handle('slug', SlugColumnHandler)
    self.handle('controls', LinkControlsHandler)
    self.handle('contact', ContactEmailHandler, person_must_exist=True)
    self.handle_raw_attr('url')
    self.handle_raw_attr('reference_url')
    self.handle_raw_attr('notes')
    self.handle('status', StatusColumnHandler, valid_states=BusinessObject.VALID_STATES)
    self.handle('sub_systems', LinkRelationshipsHandler, model_class=System,
        direction='from')
    self.handle('sub_processes', LinkRelationshipsHandler, model_class=Process,
        direction='from')
    self.handle_option('network_zone')
    self.handle('org_groups', LinkRelationshipsHandler, model_class=OrgGroup,
                 direction='from', model_human_name='Org Group')
    self.handle('vendors', LinkRelationshipsHandler, model_class=Vendor,
                 direction='from', model_human_name='Vendor')
    self.handle_date('start_date')
    self.handle_date('created_at', no_import=True)
    self.handle_date('updated_at', no_import=True)
    self.handle_text_or_html('description')
    self.handle_boolean('infrastructure', truthy_values=['infrastructure'])
    self.handle_title('title', is_required=True)

  def save_object(self, db_session, **options):
    db_session.add(self.obj)

  def after_save(self, db_session, **options):
    super(SystemRowConverter, self).after_save(db_session, **options)
    # Check whether a relationship has the program as source
    # and system as destination; if not, connect the two in session
    if options.get('parent_type'):
      program_id = options.get('parent_id')
      matching_relatinship_count = Relationship.query\
        .filter(Relationship.source_id==program_id)\
        .filter(Relationship.source_type==u'Program')\
        .filter(Relationship.destination_id==self.obj.id)\
        .filter(Relationship.destination_type==u'System')\
        .count()
      if matching_relatinship_count == 0:
        program = Program.query.get(program_id)
        if program:
            db_session.add(Relationship(
                source=program,
                context_id=program.context_id,
                destination=self.obj
            ))


class SystemsConverter(BaseConverter):

  metadata_export_order = ['type', 'slug']


  metadata_map = OrderedDict([
    ('Type','type')
  ])

  object_export_order = [
    'slug', 'title', 'description', 'notes',
    'controls', 'created_at', 'updated_at'
  ]

  object_map = OrderedDict([
    ('System Code', 'slug'),
    ('Title', 'title'),
    ('Description' , 'description'),
    ('Infrastructure', 'infrastructure'),
    ('URL', 'url'),
    ('Reference URL', 'reference_url'),
    ('Notes', 'notes'),
    ('Map:Person of Contact', 'contact'),
    ('Map:Controls', 'controls'),
    ('Map:System', 'sub_systems'),
    ('Map:Process', 'sub_processes'),
    ('Map:Org Group', 'org_groups'),
    ('Map:Vendor', 'vendors'),
    ('Effective Date', 'start_date'),
    ('Created', 'created_at'),
    ('Updated', 'updated_at'),
    ('Network Zone', 'network_zone'),
    ('State', 'status'),
  ])

  row_converter = SystemRowConverter

  def create_object_map(self):
    if self.options.get('is_biz_process'):
      self.object_map = OrderedDict( [(k.replace("System Code", 'Process Code'), v) \
                        if k == 'System Code' else (k, v) for k, v in self.object_map.items()] )

  def create_metadata_map(self):
    if self.has_parent():
      # Then put the parent code's type label in B1, slug in B2
      parent_key = '{} Code'.format(self.parent_type_string())
      parent_value = "slug"
      self.metadata_map[parent_key] = parent_value

  def validate_metadata(self, attrs):
    if self.options.get('is_biz_process'):
      self.validate_metadata_type(attrs, "Processes")
    else:
      self.validate_metadata_type(attrs, "Systems")
    self.validate_code(attrs)

  def validate_code(self, attrs):
    # Check for parent slug if importing into another object
    if self.has_parent():
      if not attrs.get('slug'):
        self.errors.append(u'Missing {} Code heading'.format(
            self.parent_type_string()))
      elif attrs['slug'] != self.parent_object().slug:
        self.errors.append(u'{0} Code must be {1}'.format(
            self.parent_type_string(), self.parent_object().slug))

  def has_parent(self):
    return bool(self.options.get('parent_type'))

  def parent_object(self):
    parent_type = self.options['parent_type']
    return parent_type.query.get(self.options['parent_id'])

  def parent_type_string(self):
    return self.options.get('parent_type').__name__

  def do_export_metadata(self):
    yield self.metadata_map.keys()
    row2 = ['Processes' if self.options.get('is_biz_process') else 'Systems']
    if self.options.get('parent_type'):
      row2.append(self.parent_object().slug)
    yield row2
    yield []
    yield []
    yield self.object_map.keys()
