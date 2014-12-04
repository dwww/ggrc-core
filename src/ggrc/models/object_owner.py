# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from sqlalchemy.ext.associationproxy import association_proxy
from sqlalchemy.ext.declarative import declared_attr
from .mixins import deferred, Mapping
from .reflection import PublishOnly

class ObjectOwner(Mapping, db.Model):
  __tablename__ = 'object_owners'

  person_id = db.Column(db.Integer, db.ForeignKey('people.id'), nullable=False)
  ownable_id = db.Column(db.Integer, nullable=False)
  ownable_type = db.Column(db.String, nullable=False)

  @property
  def ownable_attr(self):
    return '{0}_ownable'.format(self.ownable_type)

  @property
  def ownable(self):
    return getattr(self, self.ownable_attr)

  @ownable.setter
  def ownable(self, value):
    self.ownable_id = value.id if value is not None else None
    self.ownable_type = \
        value.__class__.__name__ if value is not None else None
    return setattr(self, self.ownable_attr, value)

  @staticmethod
  def _extra_table_args(cls):
    return (
        #db.UniqueConstraint('person_id', 'ownable_id', 'ownable_type'),
        db.Index('ix_object_owners_ownable', 'ownable_type', 'ownable_id'),
        )

  _publish_attrs = [
      'person',
      'ownable',
      ]

  #@classmethod
  #def eager_query(cls):
    #from sqlalchemy import orm

    #query = super(ObjectOwner, cls).eager_query()
    #return query.options(
        #orm.subqueryload('person'))

  def _display_name(self):
    return self.ownable.display_name + '<->' + self.person.display_name

class Ownable(object):
  @declared_attr
  def object_owners(cls):
    cls.owners = association_proxy(
        'object_owners', 'person',
        creator=lambda person: ObjectOwner(
          person=person,
          ownable_type=cls.__name__,
          )
        )
    joinstr = 'and_(foreign(ObjectOwner.ownable_id) == {type}.id, '\
                   'foreign(ObjectOwner.ownable_type) == "{type}")'
    joinstr = joinstr.format(type=cls.__name__)
    return db.relationship(
        'ObjectOwner',
        primaryjoin=joinstr,
        backref='{0}_ownable'.format(cls.__name__),
        cascade='all, delete-orphan',
        )

  _publish_attrs = [
      'owners',
      PublishOnly('object_owners'),
      ]

  _include_links = [
      #'object_owners',
      ]

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Ownable, cls).eager_query()
    return cls.eager_inclusions(query, Ownable._include_links).options(
        orm.subqueryload('object_owners'))
