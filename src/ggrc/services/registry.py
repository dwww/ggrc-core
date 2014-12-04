# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from collections import namedtuple
from .common import Resource

ServiceEntry = namedtuple('ServiceEntry', 'name model_class service_class')

def service(name, model_class, service_class=Resource):
  return ServiceEntry(name, model_class, service_class)
