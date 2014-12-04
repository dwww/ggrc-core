# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

from ggrc.extensions import get_extension_modules
from .roles import (
    Auditor, AuditorProgramReader, AuditorReader, ObjectEditor,
    ProgramAuditEditor, ProgramAuditOwner, ProgramAuditReader,
    ProgramBasicReader, ProgramCreator, ProgramEditor, ProgramMappingEditor,
    ProgramOwner, ProgramReader, Reader, gGRC_Admin,
    )


DECLARED_ROLE = "CODE DECLARED ROLE"


def contribute_role_permissions(permissions, additional_permissions):
  for action, resource_permissions in additional_permissions.items():
    permissions.setdefault(action, list())
    for resource_permission in resource_permissions:
      permissions[action].append(resource_permission)
  return permissions


def get_declared_role(rolename, resolved_roles={}):
  if rolename in resolved_roles:
    return resolved_roles[rolename]
  declarations = lookup_declarations()
  if rolename in declarations:
    role_definition = declarations[rolename]
    role_contributions = lookup_contributions(rolename)
    contribute_role_permissions(role_definition.permissions, role_contributions)
    resolved_roles[rolename] = role_definition
    return role_definition
  return None


def lookup_declarations(declarations={}):
  if len(declarations) == 0:
    extension_modules = get_extension_modules()
    for extension_module in extension_modules:
      ext_declarations = getattr(extension_module, "ROLE_DECLARATIONS", None)
      if ext_declarations:
        declarations.update(ext_declarations.roles())
    if len(declarations) == 0:
      declarations[None] = None
  if None in declarations:
    return {}
  else:
    return declarations


def lookup_contributions(rolename):
  extension_modules = get_extension_modules()
  contributions = {}
  for extension_module in extension_modules:
    ext_contributions = getattr(extension_module, "ROLE_CONTRIBUTIONS", None)
    if ext_contributions:
      ext_role_contributions = ext_contributions.contributions_for(rolename)
      contribute_role_permissions(contributions, ext_role_contributions)
  return contributions;


def lookup_role_implications(rolename, context_implication):
  extension_modules = get_extension_modules()
  role_implications = []
  for extension_module in extension_modules:
    ext_implications = getattr(extension_module, "ROLE_IMPLICATIONS", None)
    if ext_implications:
      role_implications.extend(
          ext_implications.implications_for(rolename, context_implication))
  return role_implications


class RoleDeclarations(object):
  """
  A RoleDeclarations object provides the names of roles declared by this
  extension.

  A role declaration is an object with 3 properties: scope, description, and
  permissions. Scope and descriptions are strings, permissions MUST be a
  dict.
  """
  def roles(self):
    return {}


class RoleContributions(object):
  """
  A RoleContributions object provides role definition dictionaries by name.
  """
  def contributions_for(self, rolename):
    """
    look up a method in self for the role name, return value of method is the
    contribution.
    """
    contributions = getattr(self.__class__, 'contributions', {})
    if rolename in contributions:
      return contributions[rolename]
    method = getattr(self.__class__, rolename, None)
    if method:
      return method(self)
    return {}


class RoleImplications(object):
  def implications_for(self, rolename, context_implication):
    """
    Return a list of rolenames implied for the given rolename, or an empty
    list.
    """
    return []


class DeclarativeRoleImplications(RoleImplications):
  implications = {}

  def implications_for(self, rolename, context_implication):
    '''Given a role assignment in context return the implied role assignments
    in src_context.
    '''
    src_context_scope = context_implication.source_context_scope
    context_scope = context_implication.context_scope
    result = self.implications.get((src_context_scope, context_scope), {})\
        .get(rolename, list())
    return result


class BasicRoleDeclarations(RoleDeclarations):
  def roles(self):
    return {
        'AuditorReader': AuditorReader,
        'Reader': Reader,
        'ProgramCreator': ProgramCreator,
        'ObjectEditor': ObjectEditor,
        'ProgramBasicReader': ProgramBasicReader,
        'ProgramMappingEditor': ProgramMappingEditor,
        'ProgramOwner': ProgramOwner,
        'ProgramEditor': ProgramEditor,
        'ProgramReader': ProgramReader,
        'AuditorProgramReader': AuditorProgramReader,
        'ProgramAuditOwner': ProgramAuditOwner,
        'ProgramAuditEditor': ProgramAuditEditor,
        'ProgramAuditReader': ProgramAuditReader,
        'Auditor': Auditor,
        }

class BasicRoleImplications(DeclarativeRoleImplications):
  # (Source Context Type, Context Type)
  #   -> Source Role -> Implied Role for Context
  implications = {
      ('Program', 'Audit'): {
        'ProgramOwner': ['ProgramAuditOwner'],
        'ProgramEditor': ['ProgramAuditEditor'],
        'ProgramReader': ['ProgramAuditReader'],
        },
      ('Audit', 'Program'): {
        'Auditor': ['AuditorProgramReader'],
        },
      ('Audit', None): {
        'Auditor': ['AuditorReader'],
        },
      ('Program', None): {
        'ProgramOwner': ['ProgramBasicReader'],
        'ProgramEditor': ['ProgramBasicReader'],
        'ProgramReader': ['ProgramBasicReader'],
        },
      (None, None): {
        'ProgramCreator': ['ObjectEditor'],
        },
      (None, 'Program'): {
        'ProgramCreator': ['ProgramMappingEditor'],
        'ObjectEditor': ['ProgramMappingEditor'],
        'Reader': ['ProgramReader'],
        },
      }
