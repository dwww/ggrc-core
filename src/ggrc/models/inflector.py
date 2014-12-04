# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""ModelInflection
* handles various naming lookups for models
* can override based on model class variables
"""

import re

def with_model_override(func):
  model_property_name = "_{0}".format(func.__name__)
  def wrapped(self):
    return getattr(self.model, model_property_name, func(self))
  return wrapped

class ModelInflector(object):
  def __new__(cls, model):
    try:
      return _inflectors[model]
    except KeyError:
      inflector = super(ModelInflector, cls).__new__(cls, model)
      _inflectors[model] = inflector
      return inflector

  def __init__(self, model):
    self.model = model
    register_inflections(self)

  def all_inflections(self):
    return {
      'model_singular': self.model_singular,
      'model_plural': self.model_plural,
      'table_singular': self.table_singular,
      'table_plural': self.table_plural,
      'human_singular': self.human_singular,
      'human_plural': self.human_plural,
      'title_singular': self.title_singular,
      'title_plural': self.title_plural,
      }

  @property
  def table_name(self):
    return self.model.__tablename__

  @property
  def model_singular(self):
    return self.model.__name__

  @property
  def model_plural(self):
    return self.title_plural.replace(' ', '')

  @property
  def table_singular(self):
    return self.underscore_from_camelcase(self.model_singular)

  @property
  @with_model_override
  def table_plural(self):
    return self.table_name

  @property
  def human_singular(self):
    return self.title_singular.lower()

  @property
  def human_plural(self):
    return self.title_plural.lower()

  @property
  def title_singular(self):
    return self.titleize_from_camelcase(self.model.__name__)

  @property
  def title_plural(self):
    return self.table_plural.replace('_', ' ').title()

  # Helpers
  @classmethod
  def underscore_from_camelcase(cls, s):
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1_\2', s)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

  @classmethod
  def titleize_from_camelcase(cls, s):
    s1 = re.sub(r'(.)([A-Z][a-z]+)', r'\1 \2', s)
    return re.sub(r'([a-z0-9])([A-Z])', r'\1 \2', s1)

  def __repr__(self):
    return (
      'ModelInflector({model}):\n'
      '  model: {model_singular} {model_plural}\n'
      '  table: {table_singular} {table_plural}\n'
      '  human: {human_singular} {human_plural}\n'
      '  title: {title_singular} {title_plural}\n')\
      .format(model=self.model, **self.all_inflections())

class ModelInflectorDescriptor(object):
  cache_attribute = '_cached_inflector'

  def __get__(self, obj, cls):
    model_inflector = getattr(cls, self.cache_attribute, None)
    if model_inflector is None or model_inflector.model is not cls:
      model_inflector = ModelInflector(cls)
      setattr(cls, self.cache_attribute, model_inflector)
    return model_inflector


# { <model class>: <ModelInflector()> }
_inflectors = {}

# { <inflection>: <model class> }
_inflection_to_model = {}

def register_inflections(inflector):
  for mode, value in inflector.all_inflections().items():
    if value in _inflection_to_model \
        and _inflection_to_model[value] is not inflector.model:
      print("Overriding inflection:\n"
            "    {0} => {1}\n"
            "  with\n"
            "    {2} => {3}".format(
              value, _inflection_to_model[value],
              value, inflector.model))
    _inflection_to_model[value] = inflector.model


def unregister_inflector(inflector):
  for mode, value in inflector.all_inflections().items():
    if value in _inflection_to_model:
      del _inflection_to_model[value]
  if inflector.model in _inflectors:
    del _inflectors[inflector.model]


def get_model(s):
  return _inflection_to_model.get(s, None)
