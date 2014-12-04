# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: vraj@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

class Cache:
  """
  Tracks modified objects in the session distinguished by
  type of modification: new, dirty and deleted.
  """
  def __init__(self):
    self.clear()

  def update_before_flush(self, session, flush_context):
    """
    Before the flush happens, we can still access to-be-deleted objects, so
    record JSON for log here
    """
    for o in session.new:
      if hasattr(o, 'log_json'):
        self.new[o] = o.log_json()
    for o in session.deleted:
      if hasattr(o, 'log_json'):
        self.deleted[o] = o.log_json()
    dirty = set(o for o in session.dirty if session.is_modified(o))
    for o in dirty - set(self.new) - set(self.deleted):
      if hasattr(o, 'log_json'):
        self.dirty[o] = o.log_json()

  def update_after_flush(self, session, flush_context):
    """
    After the flush, we know which objects were actually deleted, not just
    modified (deletes due to cascades are not known pre-flush), so fix up
    cache.
    """
    for o in self.dirty.keys():
      # SQLAlchemy magic to determine whether object was actually deleted due
      #   to `cascade="all,delete-orphan"`
      # If an object was actually deleted, move it into `deleted`
      if flush_context.is_deleted(o._sa_instance_state):
        self.deleted[o] = self.dirty[o]
        del self.dirty[o]

  def clear(self):
    self.new = {}
    self.dirty = {}
    self.deleted = {}

  def copy(self):
    copied_cache = Cache()
    copied_cache.new = dict(self.new)
    copied_cache.dirty = dict(self.dirty)
    copied_cache.deleted = dict(self.deleted)
    return copied_cache
