# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from datetime import datetime, date, timedelta
import calendar
from flask import Blueprint
from sqlalchemy import inspect

from ggrc import settings, db
from ggrc.app import app
from ggrc.login import get_current_user
from ggrc.services.registry import service
from ggrc.views.registry import object_view
from ggrc.rbac.permissions import is_allowed_update
from ggrc_basic_permissions.models import Role, UserRole, ContextImplication

import ggrc_workflows.models as models
from ggrc_workflows.models.mixins import RelativeTimeboxed

# Initialize signal handler for status changes
from blinker import Namespace
signals = Namespace()
status_change = signals.signal(
  'Status Changed',
  """
  This is used to signal any listeners of any changes in model object status
  attribute
  """)

workflow_cycle_start = signals.signal(
  'Workflow Cycle Started ',
  """
  This is used to signal any listeners of any workflow cycle start
  attribute
  """)

# Initialize Flask Blueprint for extension
blueprint = Blueprint(
  'ggrc_workflows',
  __name__,
  template_folder='templates',
  static_folder='static',
  static_url_path='/static/ggrc_workflows',
)


from ggrc.models import all_models

_workflow_object_types = [
    "Program",
    "Regulation", "Standard", "Policy", "Contract",
    "Objective", "Control", "Section", "Clause",
    "System", "Process",
    "DataAsset", "Facility", "Market", "Product", "Project"
    ]

for type_ in _workflow_object_types:
  model = getattr(all_models, type_)
  model.__bases__ = (
    #models.workflow_object.Workflowable,
    models.task_group_object.TaskGroupable,
    models.cycle_task_group_object.CycleTaskGroupable,
    models.workflow.WorkflowState,
    ) + model.__bases__
  #model.late_init_workflowable()
  model.late_init_task_groupable()
  model.late_init_cycle_task_groupable()


def get_public_config(current_user):
  """Expose additional permissions-dependent config to client.
  """
  return {}
#  public_config = {}
#  if permissions.is_admin():
#    if hasattr(settings, 'RISK_ASSESSMENT_URL'):
#      public_config['RISK_ASSESSMENT_URL'] = settings.RISK_ASSESSMENT_URL
#  return public_config


# Initialize service endpoints

def contributed_services():
  return [
      service('workflows', models.Workflow),
      service('workflow_people', models.WorkflowPerson),
      service('task_groups', models.TaskGroup),
      service('task_group_tasks', models.TaskGroupTask),
      service('task_group_objects', models.TaskGroupObject),

      service('cycles', models.Cycle),
      service('cycle_task_entries', models.CycleTaskEntry),
      service('cycle_task_groups', models.CycleTaskGroup),
      service('cycle_task_group_objects', models.CycleTaskGroupObject),
      service('cycle_task_group_object_tasks', models.CycleTaskGroupObjectTask)
      ]


def contributed_object_views():
  from . import models

  return [
      object_view(models.Workflow),
      ]


DONE_STATUSES = ("Verified",)

def _get_min_next_due_date(due_dated_objects, exclude_statuses=DONE_STATUSES):
  next_due_date = None

  for obj in due_dated_objects:
    if obj.status not in exclude_statuses:
      obj_next_due_date = obj.next_due_date
      if isinstance(obj_next_due_date, datetime):
        obj_next_due_date = obj_next_due_date.date()
      if obj_next_due_date is not None:
        if next_due_date is None or next_due_date > obj_next_due_date:
          next_due_date = obj_next_due_date

  return next_due_date


def _get_min_end_date(timeboxed_objects, exclude_statuses=DONE_STATUSES):
  end_date = None

  for obj in timeboxed_objects:
    if obj.status not in exclude_statuses:
      obj_end_date = obj.end_date
      if isinstance(obj_end_date, datetime):
        obj_end_date = obj_end_date.date()
      if obj_end_date is not None:
        if end_date is None or end_date > obj_end_date:
          end_date = obj_end_date

  return end_date


def _get_date_range(timeboxed_objects):
  start_date = None
  end_date = None

  for obj in timeboxed_objects:
    obj_start_date = obj.start_date
    if isinstance(obj_start_date, datetime):
      obj_start_date = obj_start_date.date()
    obj_end_date = obj.end_date
    if isinstance(obj_end_date, datetime):
      obj_end_date = obj_end_date.date()
    if obj_start_date is not None:
      if start_date is None or start_date > obj_start_date:
        start_date = obj_start_date
    if obj_end_date is not None:
      if end_date is None or end_date < obj_end_date:
        end_date = obj_end_date

  return (start_date, end_date)


def update_cycle_dates(cycle):
  import sqlalchemy.orm
  if cycle.id:
    # If `cycle` is already in the database, then eager load required objects
    cycle = models.Cycle.query.filter_by(id=cycle.id).\
        options(sqlalchemy.orm.joinedload_all(
          'cycle_task_groups.cycle_task_group_objects.cycle_task_group_object_tasks')).\
        one()

  for ctg in cycle.cycle_task_groups:
    for ctgo in ctg.cycle_task_group_objects:
      ctgo.start_date, ctgo.end_date = _get_date_range(
          ctgo.cycle_task_group_object_tasks)
      ctgo.next_due_date = _get_min_end_date(
          ctgo.cycle_task_group_object_tasks)

    if len(ctg.cycle_task_group_objects) == 0:
      # Handle case where cycle task group has no mapped objects
      ctg.start_date, ctg.end_date = _get_date_range(
          ctg.cycle_task_group_tasks)
      ctg.next_due_date = _get_min_end_date(
          ctg.cycle_task_group_tasks)
    else:
      ctg.start_date, ctg.end_date = _get_date_range(
          ctg.cycle_task_group_objects)
      ctg.next_due_date = _get_min_next_due_date(
          ctg.cycle_task_group_objects)
  cycle.start_date, cycle.end_date = _get_date_range(cycle.cycle_task_groups)
  cycle.next_due_date = _get_min_next_due_date(cycle.cycle_task_groups)


from ggrc.services.common import Resource

@Resource.model_posted.connect_via(models.Cycle)
def handle_cycle_post(sender, obj=None, src=None, service=None):
  if src.get('autogenerate', False):
    # When called via a REST POST, use current user.
    current_user = get_current_user()
    build_cycle(obj, current_user=current_user)


def _create_cycle_task(task_group_task, cycle, cycle_task_group, current_user,
                       frequency, base_date):
  start_date = task_group_task.calc_start_date(frequency, base_date)
  end_date = task_group_task.calc_end_date(frequency, base_date, start_date)
  cycle_task_group_object_task = models.CycleTaskGroupObjectTask(
      context=cycle.context,
      cycle=cycle,
      cycle_task_group=cycle_task_group,
      task_group_task=task_group_task,
      title=task_group_task.title,
      description=task_group_task.description,
      sort_index=task_group_task.sort_index,
      start_date=start_date,
      end_date=end_date,
      contact=task_group_task.contact,
      status="Assigned",
      modified_by=current_user,
      task_type=task_group_task.task_type,
      response_options=task_group_task.response_options,
  )
  return cycle_task_group_object_task


def build_cycle(obj, current_user=None):
  # Determine the relevant Workflow
  workflow = obj.workflow
  frequency = workflow.frequency

  # Use WorkflowOwner role when this is called via the cron job.
  if not current_user:
    for user_role in workflow.context.user_roles:
      if user_role.role.name == "WorkflowOwner":
        current_user = user_role.person
        break

  # Populate the top-level Cycle object
  obj.context = workflow.context
  obj.title = workflow.title
  obj.description = workflow.description
  obj.status = 'Assigned'

  # Find the starting date of the period containing the start date or today
  if obj.start_date:
    base_date = obj.start_date
  elif workflow.next_cycle_start_date:
    base_date = workflow.next_cycle_start_date
  else:
    base_date = date.today()

  # Populate CycleTaskGroups based on Workflow's TaskGroups
  for task_group in workflow.task_groups:
    cycle_task_group = models.CycleTaskGroup(
        context=obj.context,
        cycle=obj,
        task_group=task_group,
        title=task_group.title,
        description=task_group.description,
        end_date=obj.end_date,
        modified_by=current_user,
        contact=task_group.contact,
        sort_index=task_group.sort_index,
        )

    if len(task_group.task_group_objects) == 0:
      for task_group_task in task_group.task_group_tasks:
        cycle_task_group_object_task = _create_cycle_task(
            task_group_task, obj, cycle_task_group, current_user,
            frequency, base_date
        )
        cycle_task_group.cycle_task_group_tasks.append(
            cycle_task_group_object_task)

    for task_group_object in task_group.task_group_objects:
      object = task_group_object.object

      cycle_task_group_object = models.CycleTaskGroupObject(
          context=obj.context,
          cycle=obj,
          cycle_task_group=cycle_task_group,
          task_group_object=task_group_object,
          title=object.title,
          modified_by=current_user,
          end_date=obj.end_date,
          object=object,
          )
      cycle_task_group.cycle_task_group_objects.append(
          cycle_task_group_object)

      for task_group_task in task_group.task_group_tasks:
        cycle_task_group_object_task = _create_cycle_task(
            task_group_task, obj, cycle_task_group, current_user,
            frequency, base_date
        )
        cycle_task_group_object.cycle_task_group_object_tasks.append(
            cycle_task_group_object_task)

  update_cycle_dates(obj)

  workflow_cycle_start.send(
      obj.__class__,
      obj=obj,
      new_status=obj.status,
      old_status=None
      )

# 'InProgress' states propagate via these links
_cycle_object_parent_attr = {
    models.CycleTaskGroupObjectTask: ['cycle_task_group_object', 'cycle_task_group'],
    models.CycleTaskGroup: ['cycle']
    }

# 'Finished' and 'Verified' states are determined via these links
_cycle_object_children_attr = {
    models.CycleTaskGroupObject: ['cycle_task_group_object_tasks'],
    models.CycleTaskGroup: ['cycle_task_group_objects', 'cycle_task_group_tasks'],
    models.Cycle: ['cycle_task_groups']
    }


def update_cycle_object_child_state(obj):

  status_order = (None, 'Assigned', 'InProgress',
                  'Declined', 'Finished', 'Verified')
  status = obj.status
  children_attrs = _cycle_object_children_attr.get(type(obj), [])
  for children_attr in children_attrs:
    if children_attr:
      children = getattr(obj, children_attr, None)
      for child in children:
        if status == 'Declined' or \
           status_order.index(status) > status_order.index(child.status):
          if is_allowed_update(child.__class__.__name__, child.context.id):
            old_status = child.status
            child.status = status
            db.session.add(child)
            status_change.send(
                child.__class__,
                obj=child,
                new_status=child.status,
                old_status=old_status
            )
          update_cycle_object_child_state(child)


def update_cycle_object_parent_state(obj):
  parent_attrs = _cycle_object_parent_attr.get(type(obj), [])
  for parent_attr in parent_attrs:
    if not parent_attr:
      continue

    parent = getattr(obj, parent_attr, None)
    if not parent:
      continue

    # If any child is `InProgress`, then parent should be `InProgress`
    if obj.status == 'InProgress' or obj.status == 'Declined':
      if parent.status != 'InProgress':
        if is_allowed_update(parent.__class__.__name__, parent.context.id):
          old_status = parent.status
          parent.status = 'InProgress'
          db.session.add(parent)
          status_change.send(
              parent.__class__,
              obj=parent,
              new_status=parent.status,
              old_status=old_status
              )
        update_cycle_object_parent_state(parent)
    # If all children are `Finished` or `Verified`, then parent should be same
    elif obj.status == 'Finished' or obj.status == 'Verified':
      children_attrs = _cycle_object_children_attr.get(type(parent), [])
      for children_attr in children_attrs:
        if children_attr:
          children = getattr(parent, children_attr, None)
          children_finished = True
          children_verified = True
          for child in children:
            if child.status != 'Verified':
              children_verified = False
              if child.status != 'Finished':
                children_finished = False
          if children_verified and len(children) > 0:
            if is_allowed_update(parent.__class__.__name__, parent.context.id):
              old_status=parent.status
              parent.status = 'Verified'
              status_change.send(
                  parent.__class__,
                  obj=parent,
                  new_status=parent.status,
                  old_status=old_status
                  )
            update_cycle_object_parent_state(parent)
          elif children_finished and len(children) > 0:
            if is_allowed_update(parent.__class__.__name__, parent.context.id):
              old_status=parent.status
              parent.status = 'Finished'
              status_change.send(
                  parent.__class__,
                  obj=parent,
                  new_status=parent.status,
                  old_status=old_status
                  )
            update_cycle_object_parent_state(parent)


def ensure_assignee_is_workflow_member(workflow, assignee):
  if not assignee:
    return

  # Check if assignee is mapped to the Workflow
  workflow_people = models.WorkflowPerson.query.filter(
      models.WorkflowPerson.workflow_id == workflow.id,
      models.WorkflowPerson.person_id == assignee.id).all()
  if not workflow_people:
    workflow_person = models.WorkflowPerson(
        person=assignee,
        workflow=workflow,
        context=workflow.context
        )
    db.session.add(workflow_person)

  # Check if assignee has a role assignment
  from ggrc_basic_permissions.models import Role, UserRole
  user_roles = UserRole.query.filter(
      UserRole.context_id == workflow.context_id,
      UserRole.person_id == assignee.id).all()
  if not user_roles:
    workflow_member_role = _find_role('WorkflowMember')
    user_role = UserRole(
        person=assignee,
        role=workflow_member_role,
        context=workflow.context,
        modified_by=get_current_user(),
        )
    db.session.add(user_role)


@Resource.model_put.connect_via(models.TaskGroupTask)
def handle_task_group_task_put(sender, obj=None, src=None, service=None):
  if inspect(obj).attrs.contact.history.has_changes():
    ensure_assignee_is_workflow_member(obj.task_group.workflow, obj.contact)


@Resource.model_posted.connect_via(models.TaskGroupTask)
def handle_task_group_task_post(sender, obj=None, src=None, service=None):
  ensure_assignee_is_workflow_member(obj.task_group.workflow, obj.contact)


@Resource.model_put.connect_via(models.TaskGroup)
def handle_task_group_put(sender, obj=None, src=None, service=None):
  if inspect(obj).attrs.contact.history.has_changes():
    ensure_assignee_is_workflow_member(obj.workflow, obj.contact)


@Resource.model_posted.connect_via(models.TaskGroup)
def handle_task_group_post(sender, obj=None, src=None, service=None):
  ensure_assignee_is_workflow_member(obj.workflow, obj.contact)


@Resource.model_put.connect_via(models.CycleTaskGroupObjectTask)
def handle_cycle_task_group_object_task_put(
    sender, obj=None, src=None, service=None):
  if inspect(obj).attrs.contact.history.has_changes():
    ensure_assignee_is_workflow_member(obj.cycle.workflow, obj.contact)

  if inspect(obj).attrs.start_date.history.has_changes() \
      or inspect(obj).attrs.end_date.history.has_changes():
    update_cycle_dates(obj.cycle)

  if inspect(obj).attrs.status.history.has_changes():
    update_cycle_object_parent_state(obj)

    if obj.cycle.workflow.object_approval \
        and obj.cycle.status == 'Verified':
      for tgobj in obj.task_group_task.task_group.objects:
        old_status = tgobj.status
        tgobj.status = 'Final'
        status_change.send(
            tgobj.__class__,
            obj=tgobj,
            new_status=tgobj.status,
            old_status=old_status
            )
        db.session.add(tgobj)
      db.session.flush()


@Resource.model_put.connect_via(models.CycleTaskGroup)
def handle_cycle_task_group_put(
    sender, obj=None, src=None, service=None):
  if inspect(obj).attrs.status.history.has_changes():
    update_cycle_object_parent_state(obj)
    update_cycle_object_child_state(obj)

def update_workflow_state(workflow):
  if workflow.recurrences:
    today = date.today()
    base_date = RelativeTimeboxed._calc_base_date(today, workflow.frequency)
    workflow.next_cycle_start_date = \
      RelativeTimeboxed._calc_start_date_of_next_period(
        base_date, workflow.frequency
        )
    return

  for cycle in workflow.cycles:
    if cycle.is_current:
      return

  # No recurrences and no active cycles, workflow is now Inactive
  workflow.status = 'Inactive'
  db.session.add(workflow)
  db.session.flush()

# Check if workflow should be Inactive after end current cycle
@Resource.model_put.connect_via(models.Cycle)
def handle_cycle_put(
    sender, obj=None, src=None, service=None):
  if inspect(obj).attrs.is_current.history.has_changes():
    update_workflow_state(obj.workflow)

# Check if workflow should be Inactive after recurrence change
@Resource.model_put.connect_via(models.Workflow)
def handle_cycle_put(
    sender, obj=None, src=None, service=None):
  if inspect(obj).attrs.recurrences.history.has_changes():
    update_workflow_state(obj)


# Check if workflow should be Inactive after cycle status change
@status_change.connect_via(models.Cycle)
def handle_cycle_status_change(sender, obj=None, new_status=None, old_status=None):
  if inspect(obj).attrs.status.history.has_changes():
    if obj.status == 'Verified':
      obj.is_current = False
      db.session.add(obj)
      update_workflow_state(obj.workflow)

# FIXME: Duplicates `ggrc_basic_permissions._get_or_create_personal_context`
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


def _find_role(role_name):
  return db.session.query(Role).filter(Role.name == role_name).first()


@Resource.model_posted.connect_via(models.WorkflowPerson)
def handle_workflow_person_post(sender, obj=None, src=None, service=None):
  db.session.flush()

  # add a user_roles mapping assigning the user creating the workflow
  # the WorkflowOwner role in the workflow's context.
  workflow_member_role = _find_role('WorkflowMember')
  user_role = UserRole(
      person=obj.person,
      role=workflow_member_role,
      context=obj.context,
      modified_by=get_current_user(),
      )
  db.session.add(user_role)


@Resource.model_posted.connect_via(models.Workflow)
def handle_workflow_post(sender, obj=None, src=None, service=None):
  source_workflow = None

  if src.get('clone'):
    source_workflow_id = src.get('clone')
    source_workflow = models.Workflow.query.filter_by(
        id=source_workflow_id
        ).first()
    source_workflow.copy(obj)
    db.session.add(obj)
    db.session.flush()
    obj.title = source_workflow.title + ' (copy ' + str(obj.id) + ')'

  db.session.flush()
  # get the personal context for this logged in user
  user = get_current_user()
  personal_context = _get_or_create_personal_context(user)
  context = obj.build_object_context(
      context=personal_context,
      name='{object_type} Context {timestamp}'.format(
        object_type=service.model.__name__,
        timestamp=datetime.now()),
      description='',
      )
  context.modified_by = get_current_user()

  db.session.add(obj)
  db.session.flush()
  db.session.add(context)
  db.session.flush()
  obj.contexts.append(context)
  obj.context = context

  # add a user_roles mapping assigning the user creating the workflow
  # the WorkflowOwner role in the workflow's context.
  workflow_owner_role = _find_role('WorkflowOwner')
  user_role = UserRole(
      person=user,
      role=workflow_owner_role,
      context=context,
      modified_by=get_current_user(),
      )
  db.session.add(models.WorkflowPerson(
    person=user,
    workflow=obj,
    context=context,
    modified_by=get_current_user(),
    ))
  # pass along a temporary attribute for logging the events.
  user_role._display_related_title = obj.title
  db.session.add(user_role)
  db.session.flush()

  # Create the context implication for Workflow roles to default context
  db.session.add(ContextImplication(
      source_context=context,
      context=None,
      source_context_scope='Workflow',
      context_scope=None,
      modified_by=get_current_user(),
      ))

  if not src.get('private'):
    # Add role implication - all users can read a public workflow
    add_public_workflow_context_implication(context)

  if src.get('clone'):
    source_workflow.copy_task_groups(
      obj,
      clone_people=src.get('clone_people', False),
      clone_tasks=src.get('clone_tasks', False)
      )

    if src.get('clone_people'):
      workflow_member_role = _find_role('WorkflowMember')
      for authorization in source_workflow.context.user_roles:
        #Current user has already been added as workflow owner
        if authorization.person != user:
          db.session.add(UserRole(
            person=authorization.person,
            role=workflow_member_role,
            context=context,
            modified_by=user))
      for person in source_workflow.people:
        if person != user:
          db.session.add(models.WorkflowPerson(
            person=person,
            workflow=obj,
            context=context))


def add_public_workflow_context_implication(context, check_exists=False):
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
    context_scope='Workflow',
    modified_by=get_current_user(),
    ))


def init_extra_views(app):
  from . import views
  views.init_extra_views(app)


def start_recurring_cycles():
  today = date.today()

  # Get all workflows that should start a new cycle today
  # (The next_cycle_start_date is precomputed and stored when a cycle is created)
  workflows = db.session.query(models.Workflow)\
    .filter(
        models.Workflow.next_cycle_start_date == date.today(),
        models.Workflow.recurrences == True
        ).all()

  # For each workflow, start and save a new cycle.
  for workflow in workflows:

    cycle = models.Cycle()
    cycle.workflow = workflow
    cycle.context = workflow.context
    cycle.start_date = date.today()

    # Flag the cycle to be saved
    db.session.add(cycle)

    # Create the cycle (including all child objects)
    build_cycle(cycle)

    # Update the workflow next_cycle_start_date to push it ahead based on the frequency.
    base_date = RelativeTimeboxed._calc_base_date(today, workflow.frequency)
    workflow.next_cycle_start_date = \
      RelativeTimeboxed._calc_start_date_of_next_period(
        base_date, workflow.frequency
        )
    db.session.add(workflow)

  db.session.commit()
  db.session.flush()


from ggrc_basic_permissions.contributed_roles import (
    RoleContributions, RoleDeclarations, DeclarativeRoleImplications
    )
from ggrc_workflows.roles import (
    WorkflowOwner, WorkflowMember, BasicWorkflowReader, WorkflowBasicReader
    )


class WorkflowRoleContributions(RoleContributions):
  contributions = {
      'ProgramCreator': {
        'read': ['Workflow'],
        'create': ['Workflow'],
        },
      'ObjectEditor': {
        'read': ['Workflow'],
        'create': ['Workflow'],
        },
      'Reader': {
        'read': ['Workflow'],
        },
      'ProgramEditor': {
        'read': ['Workflow'],
        'create': ['Workflow'],
        },
      'ProgramOwner': {
        'read': ['Workflow'],
        'create': ['Workflow'],
        },
      }


class WorkflowRoleDeclarations(RoleDeclarations):
  def roles(self):
    return {
        'WorkflowOwner': WorkflowOwner,
        'WorkflowMember': WorkflowMember,
        'BasicWorkflowReader': BasicWorkflowReader,
        'WorkflowBasicReader': WorkflowBasicReader,
        }


class WorkflowRoleImplications(DeclarativeRoleImplications):
  # (Source Context Type, Context Type)
  #   -> Source Role -> Implied Role for Context
  implications = {
      (None, 'Workflow'): {
        'ProgramCreator': ['BasicWorkflowReader'],
        'ObjectEditor': ['BasicWorkflowReader'],
        'Reader': ['BasicWorkflowReader'],
        },
      ('Workflow', None): {
        'WorkflowOwner': ['WorkflowBasicReader'],
        'WorkflowMember': ['WorkflowBasicReader'],
        },
      }

ROLE_CONTRIBUTIONS = WorkflowRoleContributions()
ROLE_DECLARATIONS = WorkflowRoleDeclarations()
ROLE_IMPLICATIONS = WorkflowRoleImplications()


from ggrc_workflows.notification import notify_email_digest, notify_email_deferred
