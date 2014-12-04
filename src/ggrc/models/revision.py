# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: vraj@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from .all_models import Directive
from .mixins import Base
from .types import JsonType
from .computed_property import computed_property

class Revision(Base, db.Model):
  __tablename__ = 'revisions'

  resource_id = db.Column(db.Integer, nullable = False)
  resource_type = db.Column(db.String, nullable = False)
  event_id = db.Column(db.Integer, db.ForeignKey('events.id'), nullable = False)
  action = db.Column(db.Enum(u'created', u'modified', u'deleted'), nullable = False)
  content = db.Column(JsonType, nullable=False)

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.Index('revisions_modified_by', 'modified_by_id'),
        )

  _publish_attrs = [
      'resource_id',
      'resource_type',
      'action',
      'content',
      'description',
  ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Revision, cls).eager_query()
    return query.options(
        orm.subqueryload('modified_by'),
        )

  def __init__(self, obj, modified_by_id, action, content):
    self.resource_id = obj.id
    self.modified_by_id = modified_by_id
    self.resource_type = str(obj.__class__.__name__)
    self.action = action
    self.content = content

  @computed_property
  def description(self):
    link_objects = ['ObjectDocument']
    # TODO: Remove check below if migration can guarantee display_name in content
    if 'display_name' not in self.content:
      return ''
    display_name = self.content['display_name']
    if not display_name:
      result = u"{0} {1}".format(self.resource_type, self.action)
    elif u'<->' in display_name:
      #TODO: Fix too many values to unpack below
      source, destination = display_name.split('<->')[:2]
      if self.resource_type in link_objects:
        if self.action == 'created':
          result = u"{1} linked to {0}".format(source, destination)
        elif self.action == 'deleted':
          result = u"{1} unlinked from {0}".format(source, destination)
        else:
          result = u"{0} {1}".format(display_name, self.action)
      else:
        if self.action == 'created':
          result = u"{1} mapped to {0}".format(source, destination)
        elif self.action == 'deleted':
          result = u"{1} unmapped from {0}".format(source, destination)
        else:
          result = u"{0} {1}".format(display_name, self.action)
    else:
      if 'mapped_directive' in self.content:
        # then this is a special case of combined map/creation
        # should happen only for Section and Control
        mapped_directive = self.content['mapped_directive']
        if self.action == 'created':
          result = u"New {0}, {1}, created and mapped to {2}".format(
              self.resource_type,
              display_name,
              mapped_directive
          )
        elif self.action == 'deleted':
          result = u"{0} unmapped from {1} and deleted".format(
              display_name, mapped_directive)
        else:
          result = u"{0} {1}".format(display_name, self.action)
      else:
        # otherwise, it's a normal creation event
        result = u"{0} {1}".format(display_name, self.action)
    if self.event.action == "IMPORT":
      result += ", via spreadsheet import"
    return result
