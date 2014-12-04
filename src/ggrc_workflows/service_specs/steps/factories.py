# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com


from behave import given
from factory.fuzzy import FuzzyChoice

import tests.ggrc.behave.factories as factories

from ggrc import models
from ggrc_workflows.models import (
    Workflow, TaskGroup,
    WorkflowPerson,
    TaskGroupObject, TaskGroupTask,
    Cycle, CycleTaskEntry,
    CycleTaskGroup, CycleTaskGroupObject, CycleTaskGroupObjectTask
    )


class WorkflowFactory(factories.ModelFactory):
  MODEL = Workflow
  frequency = FuzzyChoice(MODEL.VALID_FREQUENCIES)


class TaskGroupFactory(factories.ModelFactory):
  MODEL = TaskGroup


class WorkflowPersonFactory(factories.ModelFactory):
  MODEL = WorkflowPerson
  status = FuzzyChoice(MODEL.VALID_STATES)


class TaskGroupObjectFactory(factories.ModelFactory):
  MODEL = TaskGroupObject
  object = factories.FactoryStubMarker(models.System)
  status = FuzzyChoice(MODEL.VALID_STATES)


class TaskGroupTaskFactory(factories.ModelFactory):
  MODEL = TaskGroupTask


class CycleFactory(factories.ModelFactory):
  MODEL = Cycle
  status = FuzzyChoice(MODEL.VALID_STATES)


class CycleTaskEntryFactory(factories.ModelFactory):
  MODEL = CycleTaskEntry


class CycleTaskGroupFactory(factories.ModelFactory):
  MODEL = CycleTaskGroup
  status = FuzzyChoice(MODEL.VALID_STATES)


class CycleTaskGroupObjectFactory(factories.ModelFactory):
  MODEL = CycleTaskGroupObject
  status = FuzzyChoice(MODEL.VALID_STATES)
  object = factories.FactoryStubMarker(models.System)


class CycleTaskGroupObjectTaskFactory(factories.ModelFactory):
  MODEL = CycleTaskGroupObjectTask
  status = FuzzyChoice(MODEL.VALID_STATES)


@given('Workflow factories registration')
def workflow_factories_registration(context):
  factories.WorkflowFactory = WorkflowFactory
  factories.TaskGroupFactory = TaskGroupFactory
  factories.WorkflowPersonFactory = WorkflowPersonFactory
  factories.TaskGroupObjectFactory = TaskGroupObjectFactory
  factories.TaskGroupTaskFactory = TaskGroupTaskFactory
  factories.CycleFactory = CycleFactory
  factories.CycleTaskEntryFactory = CycleTaskEntryFactory
  factories.CycleTaskGroupFactory = CycleTaskGroupFactory
  factories.CycleTaskGroupObjectFactory = CycleTaskGroupObjectFactory
  factories.CycleTaskGroupObjectTaskFactory = CycleTaskGroupObjectTaskFactory
