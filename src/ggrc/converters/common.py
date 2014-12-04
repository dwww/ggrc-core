# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

import re
from ggrc import db
from copy import *

# Temporary as I test new import functionality
DEBUG_IMPORT = True

def prepare_slug(slug):
  return re.sub(r'\r|\n'," ", slug.strip())

class ImportException(Exception):
  def __init__(self, message, show_preview=False, converter=None):
    self.message = message
    self.show_preview = show_preview
    self.converter = converter

  def __str__(self):
    return self.message if self.message else "Could not import: verify the file is correctly formatted."
