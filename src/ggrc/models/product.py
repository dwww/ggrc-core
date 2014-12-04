# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from sqlalchemy.orm import validates
from .mixins import deferred, BusinessObject, Timeboxed
from .object_control import Controllable
from .object_document import Documentable
from .object_objective import Objectiveable
from .object_owner import Ownable
from .object_person import Personable
from .object_section import Sectionable
from .relationship import Relatable
from .utils import validate_option

class Product(
    Documentable, Personable, Objectiveable, Controllable, Sectionable,
    Relatable, Timeboxed, Ownable, BusinessObject, db.Model):
  __tablename__ = 'products'

  kind_id = deferred(db.Column(db.Integer), 'Product')
  version = deferred(db.Column(db.String), 'Product')

  kind = db.relationship(
      'Option',
      primaryjoin='and_(foreign(Product.kind_id) == Option.id, '\
                       'Option.role == "product_type")',
      uselist=False,
      )

  _publish_attrs = [
      'kind',
      'version',
      ]
  _sanitize_html = [
      'version',
      ]

  @validates('kind')
  def validate_product_options(self, key, option):
    return validate_option(self.__class__.__name__, key, option, 'product_type')

  @classmethod
  def eager_query(cls):
    from sqlalchemy import orm

    query = super(Product, cls).eager_query()
    return query.options(orm.joinedload('kind'))
