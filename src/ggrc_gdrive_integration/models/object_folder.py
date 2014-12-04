# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: brad@reciprocitylabs.com

from ggrc import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from ggrc.models.mixins import deferred, Base
from ggrc.models.reflection import PublishOnly

class ObjectFolder(Base, db.Model):
  __tablename__ = 'object_folders'

  folder_id = db.Column(db.String, nullable=False)
  parent_folder_id = db.Column(db.String, nullable=True)
  folderable_id = db.Column(db.Integer, nullable=False)
  folderable_type = db.Column(db.String, nullable=False)

  @property
  def folderable_attr(self):
    return '{0}_folderable'.format(self.folderable_type)

  @property
  def folderable(self):
    return getattr(self, self.folderable_attr)

  @folderable.setter
  def folderable(self, value):
    self.folderable_id = value.id if value is not None else None
    self.folderable_type = value.__class__.__name__ if value is not None \
        else None
    return setattr(self, self.folderable_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        #db.UniqueConstraint('folder_id', 'folderable_id', 'folderable_type'),
        db.Index('ix_folderable_id_type', 'folderable_id', 'folderable_type'),
        )

  _publish_attrs = [
      'folder_id',
      'parent_folder_id',
      'folderable',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(ObjectFolder, cls).eager_query()
    return query.options()

  def _display_name(self):
    return self.folderable.display_name + '<-> gdrive folder ' + self.folder_id

class Folderable(object):
  @classmethod
  def late_init_folderable(cls):
    def make_object_folders(cls):
      joinstr = 'and_(foreign(ObjectFolder.folderable_id) == {type}.id, '\
                     'foreign(ObjectFolder.folderable_type) == "{type}")'
      joinstr = joinstr.format(type=cls.__name__)
      return db.relationship(
          'ObjectFolder',
          primaryjoin=joinstr,
          backref='{0}_folderable'.format(cls.__name__),
          cascade='all, delete-orphan',
          )
    cls.object_folders = make_object_folders(cls)

  _publish_attrs = [
      'object_folders',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Folderable, cls).eager_query()
    return query.options(
        orm.subqueryload('object_folders'))
