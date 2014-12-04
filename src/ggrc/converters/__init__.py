# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from .sections import SectionsConverter

all_converters = [
    ('sections', SectionsConverter)
    ]

def get_converter(name):
  return all_converters(name)
