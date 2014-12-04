# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com
from __future__ import absolute_import

import ggrc
import ggrc.settings
import os
import sys

def main():
  import behave.runner

  class GGRCRunner(behave.runner.Runner):
    def find_steps_paths_from_path(self, path):
      steps_dirs = []
      root_dir = behave.runner.path_getrootdir(path)

      while True:
        if os.path.isdir(os.path.join(path, 'steps')):
          steps_dirs.append(os.path.join(path, 'steps'))
        if path == root_dir:
          break
        path = os.path.dirname(path)

      return steps_dirs

    def find_steps_paths_from_paths(self, paths):
      steps_dirs = []
      # `self.config.paths` contains all paths passed on the command line
      for path in self.config.paths:
        # We use 'abspath' to normalize trailing '/' and avoid duplicates
        path = os.path.abspath(path)
        steps_dirs.extend(self.find_steps_paths_from_path(path))
      return steps_dirs

    def get_ggrc_base_path(self):
      return os.path.join(
          os.path.abspath(os.path.dirname(os.path.dirname(ggrc.__file__))),
          'service_specs')

    def load_step_definitions(self, extra_step_paths=[]):
      steps_dirs = self.find_steps_paths_from_paths(self.config.paths)
      steps_dirs = set(steps_dirs)

      # Add /src/service_specs/steps always
      steps_dirs.add(os.path.join(self.get_ggrc_base_path(), 'steps'))

      # Remove the path that `behave` *always* adds
      implicit_steps_path = os.path.join(self.base_dir, 'steps')
      steps_dirs.remove(implicit_steps_path)

      # Ensure we don't duplicate anything and only append to `extra_step_paths`
      steps_dirs.difference_update(
          [os.path.abspath(path) for path in extra_step_paths])

      return super(GGRCRunner, self).load_step_definitions(
          extra_step_paths=extra_step_paths + list(steps_dirs))

    def load_hooks(self, filename=None):
      filename = filename or \
          os.path.join(self.get_ggrc_base_path(), 'environment.py')
      return super(GGRCRunner, self).load_hooks(filename=filename)

  import behave.__main__
  # Patching the Runner class to use the modified GGRCRunner
  behave.__main__.Runner = GGRCRunner
  ret = behave.__main__.main()
  # Put things back as they were, just for general hygiene's sake
  behave.__main__.Runner = behave.runner.Runner
  return ret

if __name__ == '__main__':
  main()

