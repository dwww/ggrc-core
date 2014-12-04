# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from ggrc import db
from .mixins import Mapping

class ObjectiveControl(Mapping, db.Model):
  __tablename__ = 'objective_controls'

  @staticmethod
  def _extra_table_args(cls):
    return (
        db.UniqueConstraint('objective_id', 'control_id'),
        db.Index('ix_control_id', 'control_id'),
        db.Index('ix_objective_id', 'objective_id'),
        )

  objective_id = db.Column(db.Integer, db.ForeignKey('objectives.id'), nullable = False)
  control_id = db.Column(db.Integer, db.ForeignKey('controls.id'), nullable = False)

  _publish_attrs = [
      'objective',
      'control',
      ]

  def _display_name(self):
    return self.objective.display_name + '<->' + self.control.display_name
