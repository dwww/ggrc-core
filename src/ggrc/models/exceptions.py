# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: vraj@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

import re
from sqlalchemy.exc import IntegrityError

def field_lookup(field_string):
    """Attempts to find relevant error field for uniqueness constraint error, given SQL error message; broken off from translate_message logic
    """
    output_format = "{0}; {0}"
    bad_field = 'code'  # assumes this field as a default
    if field_string.startswith('uq_t_'):
        bad_field = 'title'
    elif field_string.endswith('email'):
        bad_field = 'email'
    return output_format.format(bad_field)

def translate_message(exception):
  """
  Translates db exceptions to something a user can understand.
  """
  message = exception.message
  if isinstance(exception, IntegrityError):
    # TODO: Handle not null, foreign key errors, uniqueness errors with compound keys
    duplicate_entry_pattern = re.compile(r'\(1062, u?"Duplicate entry (\'.*\') for key \'([^\']*)\'')
    matches = duplicate_entry_pattern.search(message)
    if matches:
      return u'The value ' + \
        matches.group(1) + \
        u' is already used for another ' + \
        field_lookup(matches.group(2)) + \
        u' values must be unique.'
    else:
      return message
  else:
    return message

class ValidationError(Exception):
  pass
