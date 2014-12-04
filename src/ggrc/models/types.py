# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: vraj@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

import sqlalchemy.types as types
import json
from ggrc.utils import as_json
from .exceptions import ValidationError

class JsonType(types.TypeDecorator):
  '''
  Marshals Python structures to and from JSON stored
  as Text in the db
  '''
  # FIXME: Change this to a larger column type and fix validation below
  impl = types.Text

  def process_result_value(self, value, dialect):
    if value is not None:
      value = json.loads(value)
    return value

  def process_bind_param(self, value, dialect):
    if value is None or isinstance(value, basestring):
      pass
    else:
      value = as_json(value)
      # Detect if the byte-length of the encoded JSON is larger than the
      # database "TEXT" column type can handle
      if len(value.encode('utf-8')) > 65534:
        raise ValidationError("Log record content too long")
    return value

class CompressedType(types.TypeDecorator):
  '''
  Marshals Python structures to and from a compressed pickle format
  as LargeBinary in the db
  '''
  impl = types.LargeBinary(length=16777215)

  def process_result_value(self, value, dialect):
    import pickle, zlib
    if value is not None:
      value = pickle.loads(zlib.decompress(value))
    return value

  def process_bind_param(self, value, dialect):
    import pickle, zlib
    value = zlib.compress(pickle.dumps(value))
    # Detect if the byte-length of the compressed pickle is larger than the
    # database "LargeBinary" column type can handle
    if len(value) > 16777215:
      raise ValidationError("Log record content too long")
    return value
