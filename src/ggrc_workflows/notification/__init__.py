# Copyright (C) 2013 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: mouli@meics.org
# Maintained By: dan@reciprocitylabs.com


from flask import current_app, request
from ggrc.app import app
import ggrc_workflows.models as models
from ggrc.notification import EmailNotification, EmailDigestNotification, isNotificationEnabled
from ggrc.notification import EmailDeferredNotification, EmailDigestDeferredNotification
from ggrc.notification import CalendarNotification, CalendarService, GGRC_CALENDAR
from ggrc.notification import create_calendar_entry, find_calendar_entry, get_calendar_event
from ggrc.notification import create_calendar_acls, delete_calendar_event
from datetime import date, timedelta
from ggrc.services.common import Resource
from ggrc.models import Person, NotificationConfig
from ggrc_basic_permissions.models import Role, UserRole
from ggrc import db
from ggrc import settings
from ggrc_workflows import status_change, workflow_cycle_start
from datetime import datetime
from werkzeug.exceptions import Forbidden
from ggrc.login import get_current_user
from sqlalchemy import inspect

PRI_CYCLE=1
PRI_TASK_OVERDUE=2
PRI_TASK_DUE=3
PRI_TASK_ASSIGNED=4
PRI_TASK_DECLINED=5
PRI_COMPLETED_TASKS=6
PRI_TASKGROUP=7
PRI_WORKFLOW_MEMBER_CHANGES=8
PRI_OTHERS=9

PRI_MAPPING={
  PRI_CYCLE: 'New Workflow cycles',
  PRI_TASK_OVERDUE: 'Tasks Due Reminder',
  PRI_TASK_DUE: 'Tasks Due today',
  PRI_TASK_ASSIGNED: 'Tasks Assigned to you',
  PRI_TASK_DECLINED: 'Your tasks that are declined',
  PRI_COMPLETED_TASKS: 'Workflow cycles with all completed tasks',
}

# ToDo(Mouli): Use pyHaml HTML templates as well sanitize input instead of embedding HTML
#
def notify_on_change(workflow):
  if workflow.notify_on_change is None:
    return False
  else:
    return workflow.notify_on_change

def get_workflow_owner(workflow):
  workflow_owner_role = Role.query.filter(Role.name == 'WorkflowOwner').first()
  user_roles = UserRole.query.filter(
      UserRole.context_id == workflow.context_id,
      UserRole.role_id == workflow_owner_role.id)
  for user_role in user_roles:
    return user_role.person

def get_task_workflow_owner(task):
  workflow=get_task_workflow(task)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: workflow is not found for task " + task.title)
    return None
  return get_workflow_owner(workflow)

def get_taskgroup_workflow_owner(task_group):
  workflow=get_taskgroup_workflow(task_group)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: workflow is not found for task group " + task_group.title)
    return None
  return get_workflow_owner(workflow)

def get_cycle_workflow_owner(cycle):
  workflow=get_cycle_workflow(cycle)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: workflow is not found for cycle" + cycle.title)
    return None
  return get_workflow_owner(workflow)

def get_task_workflow(task):
  cycle=get_cycle(task)
  if cycle is None:
    current_app.logger.warn("Notification Trigger: cycle is not found for task " + task.title)
    return None
  return get_cycle_workflow(cycle)

def get_taskgroup_workflow(task_group):
  cycle=get_taskgroup_cycle(task_group)
  if cycle is None:
    current_app.logger.warn("Notification Trigger: cycle is not found for task group " + task_group.title)
    return None
  workflow=get_cycle_workflow(cycle)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: workflow cycle is not found for task group " + task_group.title)
    return None
  return workflow

def get_task_assignee(task):
  if task.contact is not None:
    return task.contact
  task_group=get_taskgroup(task)
  if task_group is not None and task_group.contact is not None:
    return task_group.contact
  if task_group is None:
    current_app.logger.warn("Notification Trigger: task group for cycle is not found for task " + task.title)
    return None
  cycle=get_taskgroup_cycle(task_group)
  if cycle is not None and cycle is not None:
    return cycle.contact
  if cycle is None:
    current_app.logger.warn("Notification Trigger: cycle is not found for task " + task.title)
    return None

def get_cycle(task):
  task_group=get_taskgroup(task)
  if task_group is None:
    current_app.logger.warn("Notification Trigger: cycle task group is not found for task " + task.title)
    return None
  return get_taskgroup_cycle(task_group)

def get_taskgroup_cycle(task_group):
  return task_group.cycle

def get_cycle_workflow(cycle):
  return cycle.workflow

def get_taskgroup(task):
  return task.cycle_task_group

def get_task_contacts(task):
  workflow_owner=get_task_workflow_owner(task)
  if workflow_owner is None:
    current_app.logger.warn("Unable to find workflow owner for task " + task.title)
    return None
  assignee=get_task_assignee(task)
  if assignee is None:
    current_app.logger.warn("Notification Trigger: Unable to find assignee for task " + task.title)
    return None
  ret_tuple=(workflow_owner, assignee)
  return ret_tuple

def get_task_group_contacts(task_group):
  workflow_owner=get_taskgroup_workflow_owner(task_group)
  if workflow_owner is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow owner for task group " + task_group.title)
    return None
  ret_tuple=(workflow_owner, workflow_owner)
  return ret_tuple

def get_cycle_contacts(cycle):
  workflow_owner=get_cycle_workflow_owner(cycle)
  if workflow_owner is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow owner for cycle" + cycle.title)
    return None
  if cycle.contact is None:
    current_app.logger.warn("Notification Trigger: Unable to find contacts for cycle " + \
      cycle.title + " , using workflow owner as contact")
    ret_tuple=(workflow_owner, workflow_owner)
  else:
    contacts=cycle.contact
    if contacts is None:
      current_app.logger.warn("Notification Trigger: Unable to find contact information for cycle" + cycle.title)
      return None
    ret_tuple=(workflow_owner, contacts)
  return ret_tuple

def get_cycle_tasks(cycle):
  tasks_found={}
  ret_tasks=[]
  for group in cycle.cycle_task_groups:
    for task in group.cycle_task_group_tasks:
      if tasks_found.has_key(task.id):
        continue
      else:
        ret_tasks.append(task)
        tasks_found[task.id]=task
  return ret_tasks

def get_workflow_tasks(workflow):
  tasks_found={}
  ret_tasks=[]
  for group in workflow.task_groups:
    for task in group.task_group_tasks:
       if tasks_found.has_key(task.id):
         continue
       else:
         ret_tasks.append(task)
         tasks_found[task.id]=task
  return ret_tasks

def get_task_object_string(task):
  task_object = task.cycle_task_group_object
  if not task_object:
    return ""
  return " for " + task_object.title

def prepare_notification_for_task(task, sender, recipient, subject, email_content, notif_pri):
  workflow=get_task_workflow(task)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow for task " + task.title)
    return
  recipients=[recipient]
  email_digest_contents={}
  email_contents={}
  email_digest_contents[recipient.id]="<a href=" + '"'  + \
    request.url_root + "dashboard#task_widget"  + '"' + ">" + \
    task.title + "</a>"
  email_contents[recipient.id]=email_content
  override_flag=notify_on_change(workflow)
  #if notif_pri != PRI_TASK_ASSIGNED:
    #prepare_notification(task, 'Email_Deferred', notif_pri, subject, email_contents, sender, \
     #recipients, override=override_flag)
    #prepare_notification(task, 'Email_Digest_Deferred', notif_pri, subject, email_digest_contents, sender, \
     #recipients, override=False)
  #else:
  prepare_notification(task, 'Email_Now', notif_pri, subject, email_contents, sender, \
    recipients, override=override_flag)
  prepare_notification(task, 'Email_Digest', notif_pri, subject, email_digest_contents, sender, \
    recipients, override=False)

def prepare_notification_for_tasks_now(sender, recipient, subject, email_content, notif_pri):
  recipients=[recipient]
  empty_line="\n"
  email_contents={}
  email_contents[recipient.id]=email_content
  prepare_notification(recipient, 'Email_Now', notif_pri, subject, email_contents, sender, \
   recipients, override=False)

def handle_tasks_overdue():
  frequency_mapping =  {
    "weekly" : 1,
    "monthly" : 3,
    "quarterly": 7,
    "annually": 15
   }
  tasks=db.session.query(models.CycleTaskGroupObjectTask).\
    filter(models.CycleTaskGroupObjectTask.end_date > datetime.utcnow().date()).\
    filter(models.CycleTaskGroupObjectTask.status != 'Finished').\
    filter(models.CycleTaskGroupObjectTask.status != 'Verified').\
    all()

  if not len(tasks):
    return

  tasks_for_contact={}
  for task in tasks:
    cycle=get_cycle(task)
    if cycle is None:
      continue
    if cycle.is_current != True:
      continue
    contact=get_task_contacts(task)
    if contact is None:
      continue
    workflow_owner=contact[0]
    assignee=contact[1]
    if not frequency_mapping.has_key(cycle.workflow.frequency):
      continue
    num_days=frequency_mapping[cycle.workflow.frequency]
    if task.end_date != (datetime.utcnow().date() + timedelta(num_days)):
      continue
    subject="One or more tasks assigned to you are due in "  + str(num_days) + " days"
    if not tasks_for_contact.has_key(assignee.id):
      tasks_for_contact[assignee.id]=[]
    tasks_for_contact[assignee.id].append((assignee, task, subject))

  email_contents={}
  for id, items in tasks_for_contact.items():
    email_content=""
    for item in items:
      (assignee, task, subject)=item
      email_content="Hi " + assignee.name + ",<br>"  + "<p>Your tasks: <ul>"
      break
    for item in items:
      (assignee, task, subject)=item
      task_object=get_task_object_string(task)
      email_content=email_content+"<li>" + task.title + task_object + "</li>"
      email_digest_contents={}
      email_digest_contents[assignee.id]="<a href=" + '"'  + \
        request.url_root + "dashboard#task_widget"  + '"' + ">" + \
        task.title + "</a>"
      prepare_notification(assignee, 'Email_Digest', PRI_TASK_OVERDUE, subject, email_digest_contents, \
        assignee, [assignee], override=False)
    email_content=email_content + \
     "</ul></p><p>" + "Are due in " + str(num_days) + " days.</p>" + \
     "<p>Click here to view your <a href=" + '"'  + \
     request.url_root + "dashboard#task_widget"  + '"' + ">" + \
     "<b>task(s)</b></a></p>" + \
     "Thanks,<br>gGRC Team"
    prepare_notification_for_tasks_now(assignee, assignee, subject, email_content, PRI_TASK_OVERDUE)

def handle_tasks_due(num_days):
  tasks=db.session.query(models.CycleTaskGroupObjectTask).\
    filter(models.CycleTaskGroupObjectTask.end_date == (datetime.utcnow().date() + timedelta(num_days))).\
    filter(models.CycleTaskGroupObjectTask.status != 'Finished').\
    filter(models.CycleTaskGroupObjectTask.status != 'Verified').\
    all()

  if not len(tasks):
    return

  tasks_for_contact={}
  for task in tasks:
    cycle=get_cycle(task)
    if cycle is None:
      continue
    if cycle.is_current != True:
      continue
    contact=get_task_contacts(task)
    if contact is None:
      continue
    workflow_owner=contact[0]
    assignee=contact[1]
    if not tasks_for_contact.has_key(assignee.id):
      tasks_for_contact[assignee.id]=[]
    tasks_for_contact[assignee.id].append((assignee, task))

  if num_days > 0:
    num_days_text="in " + str(num_days) + " days"
  else:
    num_days_text="today"
  subject="One or more tasks assigned to you are due " + num_days_text + "!"

  for id, items in tasks_for_contact.items():
    email_content=""
    for item in items:
      (assignee, task)=item
      email_content="Hi " + assignee.name + ",<br>"  + "<p>Your tasks: <ul>"
      break
    for item in items:
      (assignee, task)=item
      task_object=get_task_object_string(task)
      email_content=email_content+"<li>" + task.title + task_object + "</li>"
      email_digest_contents={}
      email_digest_contents[assignee.id]="<a href=" + '"'  + \
        request.url_root + "dashboard#task_widget"  + '"' + ">" + \
        task.title + "</a>"
      prepare_notification(assignee, 'Email_Digest', PRI_TASK_DUE, subject, email_digest_contents, \
        assignee, [assignee], override=False)
    email_content=email_content + \
      "</ul></p><p>" + "Are due " + num_days_text + " .</p>" + \
      "<p>Click here to view your <a href=" + '"'  + \
      request.url_root + "dashboard#task_widget"  + '"' + ">" + \
      "<b>task(s)</b></a></p>" + \
      "Thanks,<br>gGRC Team"
    prepare_notification_for_tasks_now(assignee, assignee, subject, email_content, PRI_TASK_DUE)

def handle_tasks_completed_for_cycle():
  workflow_cycles=db.session.query(models.Cycle).\
    filter(models.Cycle.updated_at >= datetime.utcnow()-timedelta(1)).\
    all()
  unfinished_tasks_in_cycle={}
  for cycle in workflow_cycles:
    for task_group in cycle.cycle_task_groups:
      for task in task_group.cycle_task_group_tasks:
        if task.status not in ['Finished', 'Verified']:
          unfinished_tasks_in_cycle[cycle.id] = True
  for cycle in workflow_cycles:
    if not unfinished_tasks_in_cycle.has_key(cycle.id):
      subject="All tasks for workflow "  + cycle.title  + " are completed"
      prepare_notification_for_completed_cycle(cycle, subject, PRI_COMPLETED_TASKS)

@Resource.model_posted.connect_via(NotificationConfig)
def handle_notification_config_post(sender, obj=None, src=None, service=None):
   handle_notification_config_changes(sender, obj, src, service)

@Resource.model_put.connect_via(NotificationConfig)
def handle_notification_config_put(sender, obj=None, src=None, service=None):
   handle_notification_config_changes(sender, obj, src, service)

def handle_notification_config_changes(sender, obj=None, src=None, service=None):
  if obj.notif_type != 'Calendar':
    return
  cycles=db.session.query(models.Cycle).\
    filter(models.Cycle.is_current==True).\
    filter(models.Cycle.start_date >= datetime.utcnow().date()).all()
  user=get_current_user()
  for cycle in cycles:
    workflow=get_cycle_workflow(cycle)
    workflow_owner=get_workflow_owner(workflow)
    assignees=[]
    for person in workflow.people:
      assignees.append(person)
    #assignees.append(workflow_owner)
    for assignee in assignees:
      if assignee.id == user.id:
        enable_flag={assignee.id: obj.enable_flag}
        prepare_calendar_for_cycle(cycle, enable_flag)

def handle_new_workflow_cycle_start():
  cycles=db.session.query(models.Cycle).\
    filter(models.Cycle.is_current==True).\
    filter(models.Cycle.start_date == datetime.utcnow().date()).all()
  notify_custom_message=True
  for cycle in cycles:
    subject="New cycle of workflow  " + cycle.title + " begins today"
    prepare_notification_for_cycle(cycle, subject, " begins today", PRI_CYCLE, notify_custom_message)
    #ToDo(Mouli): Update calendar entry

@Resource.model_deleted.connect_via(models.CycleTaskGroup)
def handle_taskgroup_deleted(sender, obj=None, service=None):
  if getattr(settings, 'CALENDAR_MECHANISM', False) is False:
    return
  user=get_current_user()
  if not isNotificationEnabled(user.id, 'Calendar'):
    current_app.logger.info("Calendar Notification is not enabled for user: " + user.email)
    return
  if request.oauth_credentials is None:
    current_app.logger.error("Authorization credentials is not set for user " + user.email)
    return
    #raise Forbidden()
  from oauth2client.client import Credentials
  calendar_service=WorkflowCalendarService(Credentials.new_from_json(request.oauth_credentials))
  calendar_service.handle_taskgroup_calendar_delete(taskgroup)

@Resource.model_put.connect_via(models.CycleTaskGroupObjectTask)
def handle_task_put(sender, obj=None, src=None, service=None):
  if not (src.get('status') and getattr(obj, 'status')):
    current_app.logger.warn("Notification Trigger: Status attribute is not modified for task")
    return
  contact=get_task_contacts(obj)
  if contact is None:
    current_app.logger.warn("Notification Trigger: Unable to get task contact information")
    return
  workflow_owner=contact[0]
  assignee=contact[1]
  if inspect(obj).attrs.contact.history.has_changes():
   notif_pri=PRI_TASK_ASSIGNED
  elif inspect(obj).attrs.status.history.has_changes():
    if obj.status not in ['Declined']:
      notif_pri=PRI_OTHERS
    else:
      notif_pri=PRI_TASK_DECLINED
  else:
    return
  user=get_current_user()
  cycle=get_cycle(obj)
  task_object=get_task_object_string(obj)
  if cycle is None or object is None:
    current_app.logger.error("Unable to find cycle or object for task: " + task.title)
    return
  if notif_pri == PRI_TASK_ASSIGNED:
    subject="Task " +  obj.title + " is assigned to you"
    content="Hi " + assignee.name + ",<br>" + \
      "<p>" + user.name  + " assigned task: " + obj.title + task_object + \
      ", under workflow: " + \
      "<a href=" + '"' +  request.url_root + cycle.workflow._inflector.table_plural + \
      "/" + str(cycle.workflow.id) + "#current_widget" + '"' + \
      "<b>" + cycle.title + "</b></a></p>" + \
      "<p>Click here to view your <a href=" + '"'  + \
      request.url_root + "dashboard#task_widget"  + '"' + ">" + \
      "<b>task</b></a></p>" + \
      "Thanks,<br>gGRC Team"
  elif notif_pri == PRI_TASK_DECLINED:
    subject=user.name + " declined " +  obj.title
    content="Hi " + assignee.name + ",<br>" + \
      "<p>" + user.name  + " declined task: " + obj.title + task_object + \
      ", under workflow: " + \
      "<a href=" + '"' +  request.url_root + cycle.workflow._inflector.table_plural + \
      "/" + str(cycle.workflow.id) + "#current_widget" + '"' + \
      "<b>" + cycle.title + "</b></a></p>" + \
      "<p>Click here to view your <a href=" + '"'  + \
      request.url_root + "dashboard#task_widget"  + '"' + ">" + \
      "<b>task</b></a></p>" + \
      "Thanks,<br>gGRC Team"
  else:
    #subject="Email subject is not generated for " + obj.title  + " , status: " + obj.status
    #content="Email content is not generated for " + obj.title  + " , status: " + obj.status
    return
  prepare_notification_for_task(obj, user, assignee, subject, content, notif_pri)
  taskgroup=get_taskgroup(obj)
  if taskgroup is not None:
    prepare_calendar_for_taskgroup(taskgroup)
  else:
    current_app.logger.warn("Notification Trigger: Unable to get task group for task " + obj.title)

@Resource.model_posted.connect_via(models.WorkflowPerson)
def handle_workflow_person_post(sender, obj=None, src=None, service=None):
  person=obj.person
  workflow=obj.workflow
  subject="Member " + person.name + " is added to workflow " + workflow.title
  prepare_notification_for_workflow_member(workflow, person, subject, PRI_WORKFLOW_MEMBER_CHANGES, 'Add')

@Resource.model_deleted.connect_via(models.WorkflowPerson)
def handle_workflow_person_deleted(sender, obj=None, service=None):
  person=obj.person
  workflow=obj.workflow
  subject="Member " + person.name + " is removed from workflow " + workflow.title
  prepare_notification_for_workflow_member(workflow, person, subject, PRI_WORKFLOW_MEMBER_CHANGES, 'Remove')

def prepare_notification_for_workflow_member(workflow, member, subject, notif_pri, action):
  if not action in ['Add', 'Remove']:
    return
  found_cycle=False
  for cycle in workflow.cycles:
    if cycle.is_current:
      found_cycle=True
      break
    else:
      continue
  if not found_cycle:
    current_app.logger.warn("Notification Trigger: No Cycle has been started for workflow " + workflow.title)
    return
  #workflow_owner=get_workflow_owner(workflow)
  #if workflow_owner is None:
    #current_app.logger.warn("Notification Trigger: Unable to find workflow owner")
    #return
  #override_flag=notify_on_change(workflow)
  #empty_line="\n"
  #content=empty_line + subject + empty_line +  \
    #"  " + request.url_root + workflow._inflector.table_plural + \
    #"/" + str(workflow.id) + "#person_widget"
  to_email={}
  # custom message is set in email for new member added to workflow (not for email digest)
  #if action in ['Add'] and and workflow.notify_custom_message is not None:
    #notify_custom_message={member.id: workflow.notify_custom_message + '<br>'}
  #else:
    #notify_custom_message=None
  recipients=[]
  for person in workflow.people:
    if not to_email.has_key(person.id):
      to_email[person.id]=True
      recipients.append(person)
  if len(recipients):
    prepare_calendar_for_workflow_member(cycle, workflow, member, action)

def prepare_notification_for_completed_cycle(cycle, subject, notif_pri, notify_custom_message=False):
  workflow=get_cycle_workflow(cycle)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow for cycle")
    return
  workflow_owner=get_workflow_owner(workflow)
  if workflow_owner is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow owner for cycle")
    return
  override_flag=notify_on_change(workflow)
  empty_line="\n"
  email_contents={}
  email_digest_contents={}
  members=[workflow_owner]
  for member in members:
    email_content = "Hi " + member.name + ",<br>" + \
      "<p>All tasks for " + cycle.title + " scheduled for this cycle"
    if cycle.start_date and cycle.end_date:
      email_content = email_content + \
        "[" + cycle.start_date.strftime("%m/%d/%y") + "] - " + \
        "[" + cycle.end_date.strftime("%m/%d/%y") + "]"
    email_content = email_content + \
      " are completed </p>" + \
      "<p>Click here to view your <a href=" + '"'  + \
      request.url_root + workflow._inflector.table_plural + \
      "/" + str(workflow.id) + "#current_widget"  + '"' + ">" + \
      "<b>workflow</b></a></p>" + \
      "Thanks,<br>gGRC Team"
    email_digest_contents[member.id]= "<a href=" + '"' +  request.url_root + \
      cycle.workflow._inflector.table_plural + \
      "/" + str(cycle.workflow.id) + "#current_widget" + '"' + ">" + \
      cycle.title + "</a>"
    email_contents[member.id]=email_content

  prepare_notification(cycle, 'Email_Now', notif_pri, subject, email_contents, \
    workflow_owner, members, override=override_flag)
  prepare_notification(cycle, 'Email_Digest', notif_pri, subject, email_digest_contents, \
    workflow_owner, members, override=False)

def prepare_notification_for_cycle(cycle, subject, begins_in_days, notif_pri, notify_custom_message=False):
  workflow=get_cycle_workflow(cycle)
  if workflow is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow for cycle")
    return
  workflow_owner=get_workflow_owner(workflow)
  if workflow_owner is None:
    current_app.logger.warn("Notification Trigger: Unable to find workflow owner for cycle")
    return
  override_flag=notify_on_change(workflow)
  empty_line="\n"
  email_contents={}
  email_digest_contents={}
  #members=[workflow_owner]
  members=[]
  for people in workflow.people:
    members.append(people)
  for member in members:
    email_content = "Hi " + member.name + ",<br>" + \
      "<p>New Workflow <a href=" + '"' +  request.url_root + workflow._inflector.table_plural + \
      "/" + str(workflow.id) + "#current_widget" + '"' + ">" + \
      "<b>" + cycle.title + "</b></a>" + begins_in_days + "<br></p>"
    if notify_custom_message is True and workflow.notify_custom_message is not None:
     email_content="<p>" + email_content + workflow.notify_custom_message + "</p>"
    email_digest_contents[member.id]= "<a href=" + '"' +  request.url_root + \
      cycle.workflow._inflector.table_plural + \
      "/" + str(cycle.workflow.id) + "#current_widget" + '"' + ">" + \
      cycle.title + "</a>"
    email_contents[member.id]=email_content
    if cycle.start_date and cycle.end_date:
      email_contents[member.id]=email_contents[member.id] + \
        "<p>First cycle starts on " + cycle.start_date.strftime("%m/%d/%y") + \
        " and is due on " + cycle.end_date.strftime("%m/%d/%y") + \
        "</p>"

  task_for_contact={}
  tasks=get_cycle_tasks(cycle)
  for task in tasks:
    if task.contact:
      if not task_for_contact.has_key(task.contact.id):
        task_for_contact[task.contact.id]=[]
      task_for_contact[task.contact.id].append(task)
  for member in members:
    if task_for_contact.has_key(member.id):
      email_content=email_contents[member.id]
      if len(tasks):
        email_content=email_content + \
          "<p>You are assigned the following tasks: </p><ul>"
        tasks=task_for_contact[member.id]
        for task in tasks:
          task_object=get_task_object_string(task)
          email_content=email_content + "<li>" + \
            task.title + task_object +  ", " + \
            "due on " +  task.end_date.strftime("%m/%d/%y") +  "</li>"
        email_contents[member.id]=email_content+"</ul>"

  end_email_content= \
    "<p>" + \
    "Workflow members are:  <ul>"
  for people in workflow.people:
    if people.id != workflow_owner.id:
      end_email_content=end_email_content + \
        "<li>" + people.name + " Workflow Member </li>"
    else:
      end_email_content=end_email_content + \
        "<li>" + people.name + " Workflow Owner </li>"
  end_email_content=end_email_content + "</ul> </p>" + \
    "<p>Click here to view your <a href=" + '"'  + \
    request.url_root + "dashboard#task_widget"  + '"' + ">" + \
    "<b>tasks</b></a></p>" + \
    "Thanks,<br>gGRC Team"
  for member in members:
    email_contents[member.id]=email_contents[member.id]+end_email_content

  prepare_notification(cycle, 'Email_Now', notif_pri, subject, email_contents, \
    workflow_owner, members, override=override_flag)
  prepare_notification(cycle, 'Email_Digest', notif_pri, subject, email_digest_contents, \
    workflow_owner, members, override=False)

def prepare_notification(src, notif_type, notif_pri, subject, content, owner, recipients, \
  override=False, notify_custom_message=None):
  if notif_type == 'Email_Digest':
    emaildigest_notification = EmailDigestNotification()
    emaildigest_notification.notif_pri = notif_pri
    try:
      emaildigest_notification.prepare([src], owner, recipients, subject, content, override)
    except Exception as e:
      current_app.logger.warn("Exception occured in preparing email digest notification: " + str(e))
  elif notif_type == 'Email_Digest_Deferred':
    emaildigest_notification = EmailDigestDeferredNotification()
    emaildigest_notification.notif_pri = notif_pri
    try:
      emaildigest_notification.prepare([src], owner, recipients, subject, content, override)
    except Exception as e:
      current_app.logger.warn("Exception occured in preparing deferred email digest notification: " + str(e))
  elif notif_type == 'Email_Now':
    email_notification=EmailNotification()
    email_notification.notif_pri=notif_pri
    try:
      notification=email_notification.prepare([src], owner, recipients, subject, content, override)
    except Exception as e:
      current_app.logger.warn("Exception occured in preparing email notification: " + str(e))
      return
    if notification is not None:
      try:
        email_notification.notify_one(notification, notify_custom_message)
      except Exception as e:
        current_app.logger.warn("Exception occured in notifying email: " + str(e))
  elif notif_type == 'Email_Deferred':
    try:
      email_notification=EmailDeferredNotification()
      email_notification.notif_pri=notif_pri
      notification=email_notification.prepare([src], owner, recipients, subject, content, override)
    except Exception as e:
      current_app.logger.warn("Exception occured in preparing deferred email notification: " + str(e))

class WorkflowCalendarService(CalendarService):
  def __init__(self, credentials=None):
    super(WorkflowCalendarService, self).__init__(credentials)

  def handle_cycle_calendar_update(self, cycle, enable_flag=None):
    workflow=get_cycle_workflow(cycle)
    if workflow is None:
      current_app.logger.warn("Workflow not found for cycle " + cycle.title)
      return
    workflow_owner=get_workflow_owner(workflow)
    if workflow_owner is None:
      current_app.logger.warn("Workflow owner not found for workflow " + workflow.title)
      return
    calendar=find_calendar_entry(self.calendar_service, GGRC_CALENDAR, workflow_owner.id)
    user=get_current_user()
    if calendar is None and user.id != workflow_owner.id:
      current_app.logger.warn("Workflow owner and super user roles can create Calendar")
      return
    if calendar is None:
      calendar=create_calendar_entry(self.calendar_service, GGRC_CALENDAR, workflow_owner.id)
      if calendar is None:
        current_app.logger.error("Unable to create calendar entry for workflow " + workflow.title)
        return
        #raise Forbidden()
    calendar_event=get_calendar_event(self.calendar_service, calendar['id'], cycle.title)
    subject=cycle.title
    content=cycle.title + ' ' + request.url_root + workflow._inflector.table_plural + \
      '/' + str(workflow.id) + '#current_widget'
    notif=CalendarNotification()
    notif.start_date=cycle.start_date
    notif.end_date=cycle.end_date
    notif.notif_pri=PRI_OTHERS
    notif.calendar_service=self.calendar_service
    notif.calendar_event=calendar_event
    notif.calendar=calendar
    notif.enable_flag=enable_flag
    assignees=[]
    assignee_emails=[]
    for workflow_person in workflow.people:
      assignees.append(workflow_person)
      assignee_emails.append(workflow_person.email)
    assignees.append(workflow_owner)
    assignee_emails.append(workflow_owner.email)
    #ToDo(Mouli): WF owner and Super user can update Acl
    if user.id == workflow_owner.id:
      calendar_acls=create_calendar_acls(
        self.calendar_service,
        calendar['id'],
        assignee_emails,
        [workflow_owner.email],
        'writer')
      if calendar_acls is None:
        current_app.logger.error("Unable to create ACLs for workflow "  + workflow.title)
        return
        #raise Forbidden()
    calendar_notification = notif.prepare([cycle], workflow_owner, assignees, subject, content)
    if calendar_notification is not None:
      notif.notify_one(calendar_notification)
    # create task group related events during start of workflow
    for task_group in cycle.cycle_task_groups:
      self.handle_taskgroup_calendar_update(task_group, calendar=calendar, enable_flag=enable_flag)

  def handle_taskgroup_calendar_update(self, task_group, calendar=None, assignee=None, enable_flag=None):
    workflow=get_taskgroup_workflow(task_group)
    if workflow is None:
      current_app.logger.warn("Workflow not found for task group " + task_group.title)
      return
    cycle=get_taskgroup_cycle(task_group)
    if cycle is None:
      current_app.logger.warn("cycle not found for task group " + task_group.title)
      return
    workflow_owner=get_workflow_owner(workflow)
    if workflow_owner is None:
      current_app.logger.warn("Workflow owner not found for workflow " + workflow.title)
      return
    recipient_contacts={}
    assignees=[]
    assignee_emails=[]
    for task_group_object in task_group.cycle_task_group_objects:
      for task in task_group_object.cycle_task_group_object_tasks:
        if task.contact is not None:
          recipient_contacts[task.contact.id] = task.contact
    for id, contact in recipient_contacts.items():
      assignees.append(contact)
      assignee_emails.append(contact.email)
    user=get_current_user()
    if calendar is None:
      calendar=find_calendar_entry(self.calendar_service, GGRC_CALENDAR, workflow_owner.id)
      #ToDo(Mouli): WF owners and Superuser role can update Acl
      if calendar is None and user.id != workflow_owner.id:
        current_app.logger.error("No calendar entry is created for workflow " + workflow.title)
        return
      if calendar is None:
        calendar=create_calendar_entry(self.calendar_service, GGRC_CALENDAR, workflow_owner.id)
        if calendar is None:
          current_app.logger.error("Unable to create calendar entry for workflow " + workflow.title)
          return
          #raise Forbidden()
    calendar_event=get_calendar_event(self.calendar_service, calendar['id'], task_group.title)
    subject=task_group.title
    content=task_group.title + ' ' + request.url_root + workflow._inflector.table_plural + \
      '/' + str(workflow.id) + '#task_group_widget'
    notif=CalendarNotification()
    if task_group.start_date is None:
      notif.start_date=cycle.start_date
    else:
      notif.start_date=task_group.start_date
    if task_group.end_date is None:
      notif.end_date=cycle.end_date
    else:
      notif.end_date=task_group.end_date
    notif.notif_pri=PRI_OTHERS
    notif.calendar_service=self.calendar_service
    notif.calendar_event=calendar_event
    notif.calendar=calendar
    notif.enable_flag=enable_flag
    #ToDo(Mouli): WF owner and Super user can update Acl
    if user.id == workflow_owner.id:
      calendar_acls=create_calendar_acls(
        self.calendar_service,
        calendar['id'],
        assignee_emails,
        [workflow_owner.email],
        'writer')
      if calendar_acls is None:
        current_app.logger.error("Unable to create ACLs for workflow "  + workflow.title)
        return
        #raise Forbidden()
    calendar_notification = notif.prepare([task_group], workflow_owner, assignees, subject, content)
    if calendar_notification is not None:
      notif.notify_one(calendar_notification)

  def handle_taskgroup_calendar_delete(self, task_group):
    workflow=get_taskgroup_workflow(task_group)
    if workflow is None:
      current_app.logger.warn("Workflow not found for task group " + task_group.title)
      return
    workflow_owner=get_workflow_owner(workflow)
    if workflow_owner is None:
      current_app.logger.warn("Workflow owner not found for workflow " + workflow.title)
      return
    user=get_current_user()
    calendar=find_calendar_entry(self.calendar_service, GGRC_CALENDAR, workflow_owner.id)
    if calendar is None:
      current_app.logger.error("No calendar entry is created for workflow " + workflow.title)
      return
    calendar_event=get_calendar_event(self.calendar_service, calendar['id'], task_group.title)
    if calendar_event is None:
      current_app.logger.warn("Calendar event could not be found for task group " + task_group.title)
      return
    #ToDo(Mouli): Create notification object similar to other calendar events such as create, update
    delete_calendar_event(self.calendar_service, calendar['id'], calendar_event['id'])

def notify_email_digest():
  """ Preprocessing of tasks, cycles prior to generating email digest
  """
  handle_new_workflow_cycle_start()
  handle_tasks_overdue()
  handle_tasks_due(0)
  handle_tasks_completed_for_cycle()
  db.session.commit()

  email_digest_notification=EmailDigestNotification(priority_mapping=PRI_MAPPING)
  email_digest_notification.notify()
  db.session.commit()

def notify_email_deferred():
  """ Processing of deferred emails in particular handling Task/Undo
  """
  email_deferred=EmailDeferredNotification()
  email_deferred.notify()
  db.session.commit()

  """ Processing of deferred email digest in particular handling Task/Undo
      Marking notification type to be EmailDigest
  """
  email_digest_deferred=EmailDigestDeferredNotification()
  email_digest_deferred.notify()
  db.session.commit()

def prepare_calendar_for_cycle(cycle, enable_flag=None):
  if getattr(settings, 'CALENDAR_MECHANISM', False) is False:
    return
  user=get_current_user()
  if enable_flag is None:
   if not isNotificationEnabled(user.id, 'Calendar'):
     current_app.logger.info("Calendar Notification is not enabled for user: " + user.email)
     return
  if request.oauth_credentials is None:
    current_app.logger.error("Authorization credentials is not set for user " + user.email)
    return
    #raise Forbidden()
  from oauth2client.client import Credentials
  calendar_service=WorkflowCalendarService(Credentials.new_from_json(request.oauth_credentials))
  calendar_service.handle_cycle_calendar_update(cycle, enable_flag)

def prepare_calendar_for_workflow_member(cycle, workflow, member, action):
  if getattr(settings, 'CALENDAR_MECHANISM', False) is False:
    return
  user=get_current_user()
  if not isNotificationEnabled(user.id, 'Calendar'):
    current_app.logger.info("Calendar Notification is not enabled for user: " + user.email)
    return
  if request.oauth_credentials is None:
    current_app.logger.error("Authorization credentials is not set for user " + user.email)
    return
    #raise Forbidden()
  from oauth2client.client import Credentials
  calendar_service=WorkflowCalendarService(Credentials.new_from_json(request.oauth_credentials))
  if action in ['Remove']:
    disable_notif={member.id: False}
    calendar_service.handle_cycle_calendar_update(cycle, disable_notif)
  else:
    calendar_service.handle_cycle_calendar_update(cycle)

def prepare_calendar_for_taskgroup(taskgroup, assignee=None):
  if getattr(settings, 'CALENDAR_MECHANISM', False) is False:
    return
  user=get_current_user()
  if not isNotificationEnabled(user.id, 'Calendar'):
    current_app.logger.info("Calendar Notification is not enabled for user: " + user.email)
    return
  if request.oauth_credentials is None:
    current_app.logger.error("Authorization credentials is not set for user " + user.email)
    return
    #raise Forbidden()
  from oauth2client.client import Credentials
  calendar_service=WorkflowCalendarService(Credentials.new_from_json(request.oauth_credentials))
  calendar_service.handle_taskgroup_calendar_update(taskgroup, assignee=assignee)
