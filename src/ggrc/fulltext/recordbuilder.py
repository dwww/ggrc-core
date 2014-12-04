
# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc.models.reflection import AttributeInfo
from . import Record

class RecordBuilder(object):
  def __init__(self, tgt_class):
    self._fulltext_attrs = AttributeInfo.gather_attrs(
        tgt_class, '_fulltext_attrs')

  def as_record(self, obj):
    properties = dict([(attr, getattr(obj, attr)) \
        for attr in self._fulltext_attrs])
    return Record(
        obj.id,
        obj.__class__.__name__,
        obj.context_id,
        '', #FIXME get any qualifying fields to help in search partitioning...
        **properties
        )

def model_is_indexed(tgt_class):
  fulltext_attrs = AttributeInfo.gather_attrs(tgt_class, '_fulltext_attrs')
  return len(fulltext_attrs) > 0

def get_record_builder(obj, builders={}):
  builder = builders.get(obj.__class__.__name__)
  if builder is None:
    builder = RecordBuilder(obj.__class__)
    builders[obj.__class__.__name__] = builder
  return builder

def fts_record_for(obj):
  builder = get_record_builder(obj)
  return builder.as_record(obj)
