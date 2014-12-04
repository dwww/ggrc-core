# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc import db
from .mixins import BusinessObject, Timeboxed
from .object_control import Controllable
from .object_document import Documentable
from .object_objective import Objectiveable
from .object_owner import Ownable
from .object_person import Personable
from .object_section import Sectionable
from .relationship import Relatable

class Project(
    Documentable, Personable, Objectiveable, Controllable, Sectionable,
    Relatable, Timeboxed, Ownable, BusinessObject, db.Model):
  __tablename__ = 'projects'
