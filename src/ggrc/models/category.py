
# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.orm import validates
from .categorization import Categorization
from .mixins import deferred, Base, Hierarchical


class CategorizedPublishable(object):
  def __init__(self, attr_name, type_name):
    self.attr_name = attr_name
    self.type_name = type_name

  @property
  def rel_class(self):
    import ggrc.models
    return getattr(ggrc.models, self.type_name)

  def __call__(self, updater, obj, json_obj):
    return updater.query_for(self.rel_class, json_obj, self.attr_name, True)


class CategoryBase(Hierarchical, Base, db.Model):
  _table_plural = 'category_bases'
  __tablename__ = 'categories'

  type = db.Column(db.String)
  name = deferred(db.Column(db.String), 'CategoryBase')
  lft = deferred(db.Column(db.Integer), 'CategoryBase')
  rgt = deferred(db.Column(db.Integer), 'CategoryBase')
  scope_id = deferred(db.Column(db.Integer), 'CategoryBase')
  depth = deferred(db.Column(db.Integer), 'CategoryBase')
  required = deferred(db.Column(db.Boolean), 'CategoryBase')

  __mapper_args__ = {
      'polymorphic_on': type
      }

  categorizations = db.relationship(
      'ggrc.models.categorization.Categorization',
      backref='category', 
      cascade='all, delete-orphan',
      )

  @validates('type')
  def validates_type(self, key, value):
    return self.__class__.__name__

  # REST properties
  _publish_attrs = [
      'name',
      'type',
      'required',
      #'scope_id',
      ]
  _sanitize_html = [
      'name',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm
    query = super(CategoryBase, cls).eager_query()
    return query.options()
