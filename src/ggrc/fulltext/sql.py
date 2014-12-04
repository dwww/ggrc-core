# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from . import Indexer

class SqlIndexer(Indexer):
  def create_record(self, record, commit=True):
    for k,v in record.properties.items():
      db.session.add(self.record_type(
        key=record.key,
        type=record.type,
        context_id=record.context_id,
        tags=record.tags,
        property=k,
        content=v,
        ))
    if commit:
      db.session.commit()

  def update_record(self, record, commit=True):
    self.delete_record(record.key, record.type, commit=False)
    self.create_record(record, commit=commit)

  def delete_record(self, key, type, commit=True):
    db.session.query(self.record_type).filter(\
        self.record_type.key == key,
        self.record_type.type == type).delete()
    if commit:
      db.session.commit()

  def delete_all_records(self, commit=True):
    db.session.query(self.record_type).delete()
    if commit:
      db.session.commit()
