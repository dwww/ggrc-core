# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import os.path
import sys
from alembic import command, util, autogenerate as autogen
from alembic.config import Config, CommandLine
from alembic.environment import EnvironmentContext
from alembic.script import ScriptDirectory
from ggrc import settings
import ggrc.app
from ggrc.extensions import get_extension_module, get_extension_modules


# Monkey-patch Alembic classes to enable configuration-per-module

# Monkey-patch ScriptDirectory to allow config-specified `versions` directory
_old_ScriptDirectory_from_config = ScriptDirectory.from_config
@classmethod
def ScriptDirectory_from_config(cls, config):
  script_directory = _old_ScriptDirectory_from_config(config)
  # Override location of `versions` directory to be independent of `env.py`
  versions_location = config.get_main_option('versions_location')
  if versions_location:
    script_directory.versions = versions_location
  return script_directory
ScriptDirectory.from_config = ScriptDirectory_from_config


# Monkey-patch EnvironmentContext to override `version_table` based on
#   the config-specified extension module
_old_EnvironmentContext___init__ = EnvironmentContext.__init__
def EnvironmentContext___init__(self, config, script, **kw):
  extension_module_name = config.get_main_option('extension_module_name')
  kw['version_table'] = extension_version_table(extension_module_name)
  return _old_EnvironmentContext___init__(self, config, script, **kw)
EnvironmentContext.__init__ = EnvironmentContext___init__


# Helpers for handling migrations

def get_extension_dir(module):
  return os.path.dirname(os.path.abspath(module.__file__))

def get_extension_migrations_dir(module):
  return os.path.join(
      get_extension_dir(module),
      'migrations',
      )

def get_base_migrations_dir():
  import ggrc
  return get_extension_migrations_dir(ggrc)

def get_base_config_file():
  return os.path.join(get_base_migrations_dir(), 'alembic.ini')

def make_extension_config(extension_module_name):
  config = Config(get_base_config_file())
  # Record the current `extension_module_name` in the config to make it
  #   available to `ScriptDirectory` and `EnvironmentContext`
  config.set_main_option('extension_module_name', extension_module_name)
  module = get_extension_module(extension_module_name)
  # If the extension module contains a `migrations/env.py`, then use that,
  #   otherwise use `ggrc/migrations/env.py`
  module_script_location = get_extension_migrations_dir(module)
  if os.path.exists(os.path.join(module_script_location, 'env.py')):
    script_location = module_script_location
  else:
    script_location = get_base_migrations_dir()
  config.set_main_option('script_location', script_location)
  # Specify location of `versions` directory to be independent of `env.py`
  module_versions_location = os.path.join(module_script_location, 'versions')
  config.set_main_option('versions_location', module_versions_location)
  return config

def extension_version_table(module):
  module_name = module if type(module) is str else module.__name__
  return '{0}_alembic_version'.format(module_name)

def extension_migrations_list():
  ret = []
  for extension_module in get_extension_modules():
    migrations_dir = get_extension_migrations_dir(extension_module)
    if os.path.exists(migrations_dir):
      ret.append(migrations_dir)
  return ret

def all_extensions():
  extension_modules = ['ggrc']
  extension_modules.extend(getattr(settings, 'EXTENSIONS', []))
  return extension_modules


# Additional commands for `migrate.py` command

def upgradeall(config=None):
  '''Upgrade all modules'''
  for module_name in all_extensions():
    print("Upgrading {}".format(module_name))
    config = make_extension_config(module_name)
    command.upgrade(config, 'head')


def downgradeall(config=None, drop_versions_table=False):
  '''Downgrade all modules'''
  for module_name in reversed(all_extensions()):
    print("Downgrading {}".format(module_name))
    config = make_extension_config(module_name)
    command.downgrade(config, 'base')
    if drop_versions_table:
      from ggrc.app import db
      extension_module_name = config.get_main_option('extension_module_name')
      db.session.execute('DROP TABLE {0}'.format(
          extension_version_table(extension_module_name)))


class MigrateCommandLine(CommandLine):
  def _generate_args(self, prog):
    super(MigrateCommandLine, self)._generate_args(prog)

    # Add subparsers for `upgradeall` and `downgradeall`

    #subparsers = self.parser.add_subparsers()
    subparsers = self.parser._subparsers._actions[-1]

    downgradeall_subparser = subparsers.add_parser(
        "downgradeall", help=downgradeall.__doc__)
    downgradeall_subparser.add_argument(
        "--drop-versions-table",
        action="store_true",
        help="Drop version tables after downgrading")
    downgradeall_subparser.set_defaults(
        cmd=(downgradeall, [], ["drop_versions_table"]))

    upgradeall_subparser = subparsers.add_parser(
        "upgradeall", help=upgradeall.__doc__)
    upgradeall_subparser.set_defaults(
        cmd=(upgradeall, [], []))


def main(args):
  if len(args) < 3:
    print 'usage: migrate module_name <alembic command string>'
    return -1
  extension_module_name = args[1]

  cmd_line = MigrateCommandLine()
  options = cmd_line.parser.parse_args(args[2:])
  cfg = make_extension_config(extension_module_name)
  cmd_line.run_cmd(cfg, options)


if __name__ == '__main__':
  main(sys.argv)
