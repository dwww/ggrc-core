# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc.extensions import get_extension_instance

class Indexer(object):
  def __init__(self, settings):
    pass

  def create_record(self, record):
    raise NotImplementedError()

  def update_record(self, record):
    raise NotImplementedError()

  def delete_record(self, key):
    raise NotImplementedError()

  def search(self, terms):
    raise NotImplementedError()

class Record(object):
  def __init__(self, key, type, context_id, tags, **kwargs):
    self.key = key
    self.type = type
    self.context_id = context_id
    self.tags = tags
    self.properties = kwargs

def resolve_default_text_indexer():
  from ggrc import settings
  db_scheme = settings.SQLALCHEMY_DATABASE_URI.split(':')[0].split('+')[0]
  return 'ggrc.fulltext.{db_scheme}.Indexer'.format(db_scheme=db_scheme)

def get_indexer(indexer=[]):
  return get_extension_instance(
      'FULLTEXT_INDEXER', resolve_default_text_indexer)

