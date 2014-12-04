# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

import datetime
from flask import Blueprint, session, g
import sqlalchemy.orm
from sqlalchemy.orm.attributes import get_history
from sqlalchemy import and_, or_
from ggrc import db, settings
from ggrc.login import get_current_user, login_required
from ggrc.models.person import Person
from ggrc.models.audit import Audit
from ggrc.models.context import Context
from ggrc.models.program import Program
from ggrc.rbac import permissions
from ggrc.rbac.permissions_provider import DefaultUserPermissions
from ggrc.services.registry import service
from ggrc.services.common import Resource
from . import basic_roles
from .contributed_roles import lookup_role_implications
from .models import Role, UserRole, ContextImplication

blueprint = Blueprint(
    'permissions',
    __name__,
    template_folder='templates',
    static_folder='static',
    static_url_path='/static/ggrc_basic_permissions',
    )


def get_public_config(current_user):
  """Expose additional permissions-dependent config to client.
    Specifically here, expose GGRC_BOOTSTRAP_ADMIN values to ADMIN users.
  """
  public_config = {}
  if permissions.is_admin():
    if hasattr(settings, 'BOOTSTRAP_ADMIN_USERS'):
      public_config['BOOTSTRAP_ADMIN_USERS'] = settings.BOOTSTRAP_ADMIN_USERS
  return public_config


class CompletePermissionsProvider(object):
  def __init__(self, settings):
    pass

  def permissions_for(self, user):
    ret = UserPermissions()
    # force the permissions to be loaded into session, otherwise templates
    # that depend on the permissions being available in session may assert
    # the user has no permissions!
    ret.check_permissions()
    return ret

  def handle_admin_user(self, user):
    pass

class BasicUserPermissions(DefaultUserPermissions):
  """User permissions that aren't kept in session."""
  def __init__(self, user):
    self.user = user
    self.permissions = load_permissions_for(user)

  def _permissions(self):
    return self.permissions

class UserPermissions(DefaultUserPermissions):
  @property
  def _request_permissions(self):
    return getattr(g, '_request_permissions', None)

  @_request_permissions.setter
  def _request_permissions(self, value):
    setattr(g, '_request_permissions', value)

  def _permissions(self):
    self.check_permissions()
    return self._request_permissions

  def check_permissions(self):
    if not self._request_permissions:
      self.load_permissions()

  def get_email_for(self, user):
    return user.email if hasattr(user, 'email') else 'ANONYMOUS'

  def load_permissions(self):
    user = get_current_user()
    email = self.get_email_for(user)
    self._request_permissions = {}
    self._request_permissions['__user'] = email
    if user is None or user.is_anonymous():
      self._request_permissions = {}
    else:
      self._request_permissions = load_permissions_for(user)

def collect_permissions(src_permissions, context_id, permissions):
  for action, resource_permissions in src_permissions.items():
    if not resource_permissions:
      permissions.setdefault(action, dict())
    for resource_permission in resource_permissions:
      if type(resource_permission) in [str, unicode]:
        resource_type = str(resource_permission)
        condition = None
      else:
        resource_type = str(resource_permission['type'])
        condition = resource_permission.get('condition', None)
        terms = resource_permission.get('terms', [])
      permissions.setdefault(action, {})\
          .setdefault(resource_type, dict())\
          .setdefault('contexts', list())\
          .append(context_id)
      if condition:
        permissions[action][resource_type]\
            .setdefault('conditions', dict())\
            .setdefault(context_id, list())\
            .append({
              'condition': condition,
              'terms': terms,
              })

def load_permissions_for(user):
  """Permissions is dictionary that can be exported to json to share with
  clients. Structure is:
  ..

    permissions[action][resource_type][contexts]
                                      [conditions][context][context_conditions]

  'action' is one of 'create', 'read', 'update', 'delete'.
  'resource_type' is the name of a valid gGRC resource type.
  'contexts' is a list of context_id where the action is allowed.
  'conditions' is a dictionary of 'context_conditions' indexed by 'context'
    where 'context' is a context_id.
  'context_conditions' is a list of dictionaries with 'condition' and 'terms'
    keys.
  'condition' is the string name of a conditional operator, such as 'contains'.
  'terms' are the arguments to the 'condition'.
  """
  permissions = {}

  # Add default `Help` and `NotificationConfig` permissions for everyone
  # FIXME: This should be made into a global base role so it can be extended
  #   from extensions
  default_permissions = {
      "read": [
        "Help",
        {
          "type": "NotificationConfig",
          "terms": {
            "property_name": "person",
            "value": "$current_user"
            },
          "condition": "is"
        },
        ],
      "create": [
        {
          "type": "NotificationConfig",
          "terms": {
            "property_name": "person",
            "value": "$current_user"
            },
          "condition": "is"
        },
        ],
      "update": [
        {
          "type": "NotificationConfig",
          "terms": {
            "property_name": "person",
            "value": "$current_user"
            },
          "condition": "is"
        },
        ]
      }
  collect_permissions(default_permissions, None, permissions)

  # Add `ADMIN_PERMISSION` for "bootstrap admin" users
  if hasattr(settings, 'BOOTSTRAP_ADMIN_USERS') \
      and user.email in settings.BOOTSTRAP_ADMIN_USERS:
    admin_permissions = {
        DefaultUserPermissions.ADMIN_PERMISSION.action: [
          DefaultUserPermissions.ADMIN_PERMISSION.resource_type
          ]
        }
    collect_permissions(
        admin_permissions,
        DefaultUserPermissions.ADMIN_PERMISSION.context_id,
        permissions)

  # Now add permissions from all DB-managed roles
  user_roles = db.session.query(UserRole)\
      .options(
          sqlalchemy.orm.undefer_group('UserRole_complete'),
          sqlalchemy.orm.undefer_group('Role_complete'),
          sqlalchemy.orm.joinedload('role'))\
      .filter(UserRole.person_id==user.id)\
      .order_by(UserRole.updated_at.desc())\
      .all()

  source_contexts_to_rolenames = {}
  for user_role in user_roles:
    source_contexts_to_rolenames.setdefault(
        user_role.context_id,list()).append(user_role.role.name)
    if isinstance(user_role.role.permissions, dict):
      collect_permissions(
          user_role.role.permissions, user_role.context_id, permissions)

  # apply role implications per context implication
  all_context_implications = db.session.query(ContextImplication)
  keys = [k for k in source_contexts_to_rolenames.keys() if k is not None]
  if keys and None in source_contexts_to_rolenames:
    all_context_implications = all_context_implications.filter(
        or_(
          ContextImplication.source_context_id == None,
          ContextImplication.source_context_id.in_(keys),
          )).all()
  elif keys:
    all_context_implications = all_context_implications.filter(
          ContextImplication.source_context_id.in_(keys)).all()
  elif None in source_contexts_to_rolenames:
    all_context_implications = all_context_implications.filter(
          ContextImplication.source_context_id == None).all()
  else:
    all_context_implications = []

  # Gather all roles required by context implications
  implied_context_to_implied_roles = {}
  all_implied_roles_set = set()
  for context_implication in all_context_implications:
    for rolename in source_contexts_to_rolenames.get(
        context_implication.source_context_id, []):
      implied_role_names_list = implied_context_to_implied_roles.setdefault(
          context_implication.context_id, list())
      implied_role_names = lookup_role_implications(
          rolename, context_implication)
      all_implied_roles_set.update(implied_role_names)
      implied_role_names_list.extend(implied_role_names)
  # If some roles are required, query for them in bulk
  all_implied_roles_by_name = {}
  if implied_context_to_implied_roles:
    implied_roles = db.session.query(Role)\
        .filter(Role.name.in_(all_implied_roles_set))\
        .options(sqlalchemy.orm.undefer_group('Role_complete'))\
        .all()
    for implied_role in implied_roles:
      all_implied_roles_by_name[implied_role.name] = implied_role
  # Now aggregate permissions resulting from these roles
  for implied_context_id, implied_rolenames \
      in implied_context_to_implied_roles.items():
    for implied_rolename in implied_rolenames:
      implied_role = all_implied_roles_by_name[implied_rolename]
      collect_permissions(
          implied_role.permissions, implied_context_id, permissions)

  personal_context = _get_or_create_personal_context(user)

  permissions.setdefault('__GGRC_ADMIN__',{})\
      .setdefault('__GGRC_ALL__', dict())\
      .setdefault('contexts', list())\
      .append(personal_context.id)
  return permissions


def _get_or_create_personal_context(user):
  personal_context = user.get_or_create_object_context(
      context=1,
      name='Personal Context for {0}'.format(user.id),
      description='',
      )
  personal_context.modified_by = get_current_user()
  db.session.add(personal_context)
  db.session.flush()
  return personal_context


@Resource.model_posted.connect_via(Program)
def handle_program_post(sender, obj=None, src=None, service=None):
  db.session.flush()
  # get the personal context for this logged in user
  user = get_current_user()
  personal_context = _get_or_create_personal_context(user)
  context = obj.build_object_context(
      context=personal_context,
      name='{object_type} Context {timestamp}'.format(
        object_type=service.model.__name__,
        timestamp=datetime.datetime.now()),
      description='',
      )
  context.modified_by = get_current_user()

  db.session.add(obj)
  db.session.flush()
  db.session.add(context)
  db.session.flush()
  obj.contexts.append(context)
  obj.context = context

  # add a user_roles mapping assigning the user creating the program
  # the ProgramOwner role in the program's context.
  program_owner_role = basic_roles.program_owner()
  user_role = UserRole(
      person=get_current_user(),
      role=program_owner_role,
      context=context,
      modified_by=get_current_user(),
      )
  #pass along a temporary attribute for logging the events.
  user_role._display_related_title = obj.title
  db.session.add(user_role)
  db.session.flush()

  #Create the context implication for Program roles to default context
  db.session.add(ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='Program',
      context_scope=None,
      modified_by=get_current_user(),
      ))

  if not src.get('private'):
    # Add role implication - all users can read a public program
    add_public_program_context_implication(context)


def add_public_program_context_implication(context, check_exists=False):
  if check_exists and db.session.query(ContextImplication)\
      .filter(
          and_(
            ContextImplication.context_id == context.id,
            ContextImplication.source_context_id == None))\
      .count() > 0:
    return
  db.session.add(ContextImplication(
    source_context=None,
    context=context,
    source_context_scope=None,
    context_scope='Program',
    modified_by=get_current_user(),
    ))


@Resource.model_put.connect_via(Program)
def handle_program_put(sender, obj=None, src=None, service=None):
  #Check to see if the private property of the program has changed
  if get_history(obj, 'private').has_changes():
    if obj.private:
      # Ensure that any implications from null context are removed
      implications = db.session.query(ContextImplication)\
          .filter(
              ContextImplication.context_id == obj.context_id,
              ContextImplication.source_context_id == None)\
                  .delete()
      db.session.flush()
    else:
      #ensure that implications from null are present
      add_public_program_context_implication(obj.context, check_exists=True)
      db.session.flush()


@Resource.model_posted.connect_via(Audit)
def handle_audit_post(sender, obj=None, src=None, service=None):
  db.session.flush()
  #Create an audit context
  context = obj.build_object_context(
      context=obj.context,
      name='Audit Context {timestamp}'.format(
        timestamp=datetime.datetime.now()),
      description='',
      )
  context.modified_by = get_current_user()
  db.session.add(context)
  db.session.flush()

  #Create the program -> audit implication
  db.session.add(ContextImplication(
    source_context=obj.context,
    context=context,
    source_context_scope='Program',
    context_scope='Audit',
    modified_by=get_current_user(),
    ))

  #Create the audit -> program implication
  db.session.add(ContextImplication(
    source_context=context,
    context=obj.context,
    source_context_scope='Audit',
    context_scope='Program',
    modified_by=get_current_user(),
    ))

  db.session.add(obj)

  #Create the role implication for Auditor from Audit for default context
  db.session.add(ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='Audit',
      context_scope=None,
      modified_by=get_current_user(),
      ))
  db.session.flush()

  #Place the audit in the audit context
  obj.context = context


@Resource.model_deleted.connect
def handle_resource_deleted(sender, obj=None, service=None):
  if obj.context \
      and obj.context.related_object_id \
      and obj.id == obj.context.related_object_id \
      and obj.__class__.__name__ == obj.context.related_object_type:
    db.session.query(UserRole) \
        .filter(UserRole.context_id == obj.context_id) \
        .delete()
    db.session.query(ContextImplication) \
        .filter(
            or_(
              ContextImplication.context_id == obj.context_id,
              ContextImplication.source_context_id == obj.context_id
              ))\
        .delete()
    # Deleting the context itself is problematic, because unattached objects
    #   may still exist and cause a database error.  Instead of implicitly
    #   cascading to delete those, just leave the `Context` object in place.
    #   It and its objects will be visible *only* to Admin users.
    #db.session.delete(obj.context)

# Removed because this is now handled purely client-side, but kept
# here as a reference for the next one.
# @BaseObjectView.extension_contributions.connect_via(Program)
def contribute_to_program_view(sender, obj=None, context=None):
  if obj.context_id != None and \
      permissions.is_allowed_read('Role', 1) and \
      permissions.is_allowed_read('UserRole', obj.context_id) and \
      permissions.is_allowed_create('UserRole', obj.context_id) and \
      permissions.is_allowed_update('UserRole', obj.context_id) and \
      permissions.is_allowed_delete('UserRole', obj.context_id):
    return 'permissions/programs/_role_assignments.haml'
  return None

from ggrc.app import app
@app.context_processor
def authorized_users_for():
  return {'authorized_users_for': UserRole.role_assignments_for,}


def contributed_services():
  """The list of all collections provided by this extension."""
  return [
      service('roles', Role),
      service('user_roles', UserRole),
      ]


def contributed_object_views():
  from ggrc.views.registry import object_view
  return [
      object_view(Role)
      ]


from .contributed_roles import BasicRoleDeclarations, BasicRoleImplications
ROLE_DECLARATIONS = BasicRoleDeclarations()
ROLE_IMPLICATIONS = BasicRoleImplications()

# standard decorator style
from sqlalchemy import event
from sqlalchemy.orm import make_transient
@event.listens_for(Person.is_enabled, 'set')
def receive_set(target, value, oldvalue, initiator):
  "listen for the the is_enabled flag to be set to False"

  if value is False:
    # Delete UserRoles related to the Person
    db.session.query(UserRole).filter(UserRole.person_id==target.id).delete()
    db.session.commit()
