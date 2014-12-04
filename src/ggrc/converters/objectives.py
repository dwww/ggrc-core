# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: silas@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from .base import *
from ggrc.models import Control, Directive, Policy, Program, Regulation, Contract, Standard, Section, Objective, ObjectObjective, SectionObjective
from ggrc.models.mixins import BusinessObject
from .base_row import *
from collections import OrderedDict

DIRECTIVE_CLASSES = [Directive, Policy, Regulation, Contract, Standard]

class ObjectiveRowConverter(BaseRowConverter):
  model_class = Objective

  def find_by_slug(self, slug):
    from sqlalchemy import orm
    return self.model_class.query.filter_by(slug=slug).options(
        orm.joinedload('object_objectives')).first()

  def setup_object(self):
    self.obj = self.setup_object_by_slug(self.attrs)
    if self.obj.id is not None:
      self.add_warning('slug', "Objective already exists and will be updated")

  def reify(self):
    self.handle('slug', SlugColumnHandler)
    self.handle_title('title', is_required=True)
    self.handle_text_or_html('description')
    self.handle_raw_attr('url')
    self.handle_raw_attr('reference_url')
    self.handle_text_or_html('notes')
    self.handle_date('created_at', no_import=True)
    self.handle_date('updated_at', no_import=True)
    self.handle('section', LinkSectionObjective)
    self.handle('control', LinkControlObjective)
    self.handle('contact', ContactEmailHandler, person_must_exist=True)
    self.handle('status', StatusColumnHandler, valid_states=BusinessObject.VALID_STATES)

  def save_object(self, db_session, **options):
    db_session.add(self.obj)

  def after_save(self, db_session, **options):
    super(ObjectiveRowConverter, self).after_save(db_session, **options)
    # use self.options, which will, if relevant, be overwritten
    # with data about section instead of directive
    parent_type = self.options.get('parent_type')
    parent_id = self.options.get('parent_id')
    # always connect to directive; if parent is section/clause,
    # find the directive through it
    if parent_type in DIRECTIVE_CLASSES or parent_type == Program:
      parent_obj = parent_type.query.get(parent_id)
      parent_string = unicode(parent_obj.__class__.__name__)
      # check if no such directive/object mapping exists; if none, add
      matching_relationship_count = ObjectObjective.query\
        .filter(ObjectObjective.objectiveable_id==parent_id)\
        .filter(ObjectObjective.objectiveable_type==parent_string)\
        .filter(ObjectObjective.objective_id==self.obj.id)\
        .count()
      if matching_relationship_count == 0:
        db_options = {
                "objectiveable_type": parent_string,
                "objectiveable_id": parent_id,
                "objective": self.obj,
        }
        if parent_type == Program:
          db_options["context_id"] = parent_obj.context_id
        db_session.add(ObjectObjective(**db_options))


class ObjectivesConverter(BaseConverter):

  metadata_map = OrderedDict([
    ('Type', 'type'),
    ('Directive Code', 'slug')
  ])

  object_map = OrderedDict([
    ('Objective Code', 'slug'),
    ('Title', 'title'),
    ('Description', 'description'),
    ('URL', 'url'),
    ('Reference URL', 'reference_url'),
    ('Notes', 'notes'),
    ('Created', 'created_at'),
    ('Updated', 'updated_at'),
    ('Map:Section', 'section'),
    ('Map:Control', 'control'),
    ('Map:Person of Contact', 'contact'),
    ('State', 'status'),
  ])

  row_converter = ObjectiveRowConverter

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
    self.validate_metadata_type(attrs, "Objectives")
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
    yield ['Objectives', self.parent_object().slug]
    yield[]
    yield[]
    yield self.object_map.keys()

