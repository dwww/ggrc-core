# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

from datetime import date, timedelta
from tests.ggrc import TestCase
from ggrc_workflows.services.workflow_date_calculator import WorkflowDateCalculator
from ggrc_workflows.models import *
from ggrc.models import *

class BaseWorkflowDateCalculator(TestCase):
  SQLALCHEMY_DATABASE_URI = "sqlite://"

  def setUp(self):
    pass

  def tearDown(self):
    pass

  def _workflow_factory(self):
    workflow = Workflow()
    workflow.id = 1
    return workflow

  def _create_one_time_workflow(self):
    # Create one-time workflow
    workflow = self._workflow_factory()
    workflow.id = 1
    workflow.frequency = "one_time"
    workflow.title = "One Time Workflow"
    return workflow

  def _create_weekly_workflow(self):
    # Create one-time workflow
    workflow = self._workflow_factory()
    workflow.frequency = "weekly"
    workflow.title = "Weekly Workflow"
    return workflow

  def _create_monthly_workflow(self):
    # Create one-time workflow
    workflow = self._workflow_factory()
    workflow.frequency = "monthly"
    workflow.title = "Monthly Workflow"
    return workflow

  def _create_quarterly_workflow(self):
    # Create one-time workflow
    workflow = self._workflow_factory()
    workflow.frequency = "quarterly"
    workflow.title = "Quarterly Workflow"
    return workflow

  def _create_annual_workflow(self):
    # Create one-time workflow
    workflow = self._workflow_factory()
    workflow.frequency = "annually"
    workflow.title = "Annual Workflow"
    return workflow

  def _set_date_range_for_workflow(self, workflow, start_date, end_date):
    task_group = TaskGroup()
    task_group.id = 1
    task_group.workflow_id = workflow.id
    task_group.title = workflow.title
    workflow.task_groups.append(task_group)

    task_group_task = TaskGroupTask()
    task_group_task.id = 1
    task_group_task.task_group_id = task_group.id
    task_group_task.title = "Task: "+workflow.title
    # FIXME I did this to normalize the test API to take just dates, while TaskGroupTasks
    # FIXME store relative start|end month|day for non one_time workflows, and
    # FIXME start|end dates for one_time workflows.
    if "one_time" == workflow.frequency:
      task_group_task.start_date = start_date
      task_group_task.end_date = end_date
    else:
      if "weekly" == workflow.frequency:
        task_group_task.relative_start_month=None
        task_group_task.relative_start_day=start_date.isoweekday()
        task_group_task.relative_end_month=None
        task_group_task.relative_end_day=end_date.isoweekday()
      elif "monthly" == workflow.frequency:
        task_group_task.relative_start_month=None
        task_group_task.relative_start_day=start_date.day
        task_group_task.relative_end_month=None
        task_group_task.relative_end_day=end_date.day
      elif "quarterly" == workflow.frequency:
        sm = start_date.month % 3
        if 0 == sm:
          sm = 3
        em = end_date.month % 3
        if 0 == em:
          em = 3
        task_group_task.relative_start_month=sm
        task_group_task.relative_start_day=start_date.day
        task_group_task.relative_end_month=em
        task_group_task.relative_end_day=end_date.day
      elif "annually" == workflow.frequency:
        task_group_task.relative_start_month=start_date.month
        task_group_task.relative_start_day=start_date.day
        task_group_task.relative_end_month=end_date.month
        task_group_task.relative_end_day=end_date.day
      else:
        pass

    task_group.task_group_tasks.append(task_group_task)

    # Use DataAsset because it just has a title. Easy to work with.
    data_asset = DataAsset()
    data_asset.id = 1
    data_asset.title = "Data Asset: "+workflow.title

    task_group_object = TaskGroupObject()
    task_group_object.id = 1
    task_group_object.task_group_id=task_group.id
    task_group_object.object_id = data_asset.id
    task_group_object.object_type = data_asset.type
    task_group.task_group_objects.append(task_group_object)

    return workflow

  def cycle_for_workflow(self, workflow):
    cycle = Cycle()
    cycle.workflow = workflow
    cycle.title = workflow.title
    cycle.description = workflow.description
    return cycle

  def today(self):
    return date.today()

  def tomorrow(self):
    return self.today() + timedelta(days=1)

  def day_after_tomorrow(self):
    return self.today() + timedelta(days=2)

  def yesterday(self):
    return self.today() + timedelta(days=-1)

  def day_before_yesterday(self):
    return self.today() + timedelta(days=-2)

  def seven_days_ago(self):
    return self.today()+ timedelta(days=-7)

  def seven_days_from_now(self):
    return self.today() + timedelta(days=7)

  def thirty_days_ago(self):
    return self.today() + timedelta(days=-30)

  def thirty_days_from_now(self):
    return self.today() + timedelta(days=30)

  def one_year_ago(self):
    return self.today() + timedelta(weeks=-52)

  def one_year_from_now(self):
    return self.today() + timedelta(weeks=52)

  def day_this_week(self, weekday_number):
    day = self.today()
    while day.isoweekday() < weekday_number:
      day = day + timedelta(days=1)
    while day.isoweekday() > weekday_number:
      day = day + timedelta(days=-1)
    return day

  def monday(self):
    return self.day_this_week(1)

  def tuesday(self):
    return self.day_this_week(2)

  def wednesday(self):
    return self.day_this_week(3)

  def thursday(self):
    return self.day_this_week(4)

  def friday(self):
    return self.day_this_week(5)

  def saturday(self):
    return self.day_this_week(6)

  def sunday(self):
    return self.day_this_week(7)

  def day_this_month(self, day_number):
    day = self.today()
    while day.day < day_number:
      day = day + timedelta(days=1)
    while day.day > day_number:
      day = day + timedelta(days=-1)
    return day

  def day_this_year(self, month, day):
    return date(date.today().year, month, day)

  def day_next_year(self, month, day):
    return date(date.today().year+1, month, day)


class TestOneTimeWorkflow(BaseWorkflowDateCalculator):
  def test_start_date_sets_properly(self):
    workflow = self._create_one_time_workflow()
    workflow = \
      self._set_date_range_for_workflow(workflow,self.tuesday(),self.friday())

    self.assertEqual(1, len(workflow.task_groups))

    calc = WorkflowDateCalculator(workflow)

    start_day = calc._min_relative_start_day_from_tasks()
    start_month = calc._min_relative_start_month_from_tasks()
    end_day = calc._max_relative_end_day_from_tasks()
    end_month = calc._max_relative_end_month_from_tasks()

    self.assertEqual(start_day, self.tuesday().day)
    self.assertEqual(start_month, self.tuesday().month)
    self.assertEqual(end_day, self.friday().day)
    self.assertEqual(end_month, self.friday().month)

  def test_calc_start_date_one_time_workflow(self):
    workflow = self._create_one_time_workflow()
    workflow = \
      self._set_date_range_for_workflow(workflow,self.wednesday(),self.friday())

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(self.monday())
    self.assertEqual(start_date, self.wednesday())

  def test_one_time_workflow_previous_start_date(self):
    mar_1 = self.day_this_year(3, 1)
    workflow = self._create_one_time_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_year(3,4), self.day_this_year(8,24))
    calculator = WorkflowDateCalculator(workflow)
    start_date = calculator.nearest_start_date_after_basedate(mar_1)
    self.assertEqual(start_date, self.day_this_year(3, 4))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(8, 24))
    previous_cycle_start_date = calculator.previous_cycle_start_date_before_basedate(mar_1)
    self.assertEqual(start_date, previous_cycle_start_date)

  def test_start_day_in_past(self):
    past = self.seven_days_ago()
    today = self.today()
    future = self.seven_days_from_now()

    workflow = self._set_date_range_for_workflow(
        self._create_one_time_workflow(),
        past,
        future)
    calc = WorkflowDateCalculator(workflow)

    self.assertEqual(calc.nearest_start_date_after_basedate(today), past)
    self.assertEqual(calc.nearest_end_date_after_start_date(today), future)


  def test_start_and_end_date_in_past(self):
    month_ago = self.thirty_days_ago()
    week_ago = self.seven_days_ago()
    today = self.today()

    workflow = self._set_date_range_for_workflow(
        self._create_one_time_workflow(),
        month_ago,
        week_ago)
    calc = WorkflowDateCalculator(workflow)

    self.assertEqual(calc.nearest_start_date_after_basedate(today), month_ago)
    self.assertEqual(calc.nearest_end_date_after_start_date(month_ago), week_ago)

  def test_end_date_before_start_date(self):
    month_ago = self.thirty_days_ago()
    week_ago = self.seven_days_ago()

    workflow = self._set_date_range_for_workflow(
        self._create_one_time_workflow(),
        week_ago,
        month_ago
    )
    calc = WorkflowDateCalculator(workflow)

    with self.assertRaises(ValueError):
        calc.nearest_end_date_after_start_date(week_ago)


class TestWeeklyWorkflow(BaseWorkflowDateCalculator):
  def test_calc_end_date_weekly_workflow_start_before_end(self):
    workflow = self._create_weekly_workflow()
    workflow = \
      self._set_date_range_for_workflow(workflow,self.tuesday(),self.thursday())

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(self.monday())
    self.assertEqual(start_date, self.tuesday())

  def test_weekly_workflow_basedate_after_start_date(self):
    workflow = self._create_weekly_workflow()
    workflow = \
      self._set_date_range_for_workflow(workflow, self.tuesday(), self.thursday())

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(self.wednesday())
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.wednesday() + timedelta(days=6))
    self.assertEqual(end_date, start_date + timedelta(days=2))

  def test_weekly_workflow_basedate_before_start_date(self):
    workflow = self._create_weekly_workflow()
    wednesday = self.wednesday()
    friday = self.friday()
    workflow = \
      self._set_date_range_for_workflow(workflow, self.wednesday(), self.friday())

    tuesday = self.tuesday()

    # day_1 is a Tuesday
    # start_date is a Wednesday
    # end_date is a Friday

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(tuesday)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, tuesday + timedelta(days=1))
    self.assertEqual(end_date, start_date + timedelta(days=2))

  def test_weekly_workflow_end_day_before_start_day_basedate_before_start_day(self):
    workflow = self._create_weekly_workflow()
    workflow = \
      self._set_date_range_for_workflow(workflow, self.thursday(), self.tuesday())

    tuesday = self.tuesday()

    # day_1 is a Tuesday
    # start_date is a Thursday
    # end_date is a Tuesday

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(tuesday)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, tuesday + timedelta(days=2))
    self.assertEqual(end_date, start_date + timedelta(days=5))

  def test_weekly_workflow_end_day_equals_start_day_basedate_before_start_day(self):
    workflow = self._create_weekly_workflow()
    workflow = \
      self._set_date_range_for_workflow(workflow, self.wednesday(), self.wednesday())

    tuesday = self.tuesday()
    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(tuesday)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, tuesday + timedelta(days=1))
    self.assertEqual(end_date, start_date)

  def test_weekly_workflow_end_day_equals_start_day_basedate_equals_start_day(self):
    workflow = self._create_weekly_workflow()
    start_date = self.tuesday()
    end_date = self.tuesday()
    workflow = \
      self._set_date_range_for_workflow(workflow, start_date, end_date)

    tuesday = self.tuesday()
    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(tuesday)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, tuesday)
    self.assertEqual(end_date, start_date)


class TestMonthlyWorkflow(BaseWorkflowDateCalculator):
  def test_monthly_workflow_calc_start_and_end_date_after_basedate(self):
    workflow = self._create_monthly_workflow()
    day_5 = self.day_this_month(5)
    day_10 = self.day_this_month(10)
    workflow = self._set_date_range_for_workflow(workflow, day_5, day_10)
    day_4 = self.day_this_month(4)
    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(day_4)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, day_4 + timedelta(days=1))
    self.assertEqual(end_date, start_date + timedelta(days=5))

  def test_monthly_workflow_calc_start_date_on_basedate(self):
    workflow = self._create_monthly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_month(5), self.day_this_month(10))
    day_5 = self.day_this_month(5)
    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(day_5)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, day_5)
    self.assertEqual(end_date, start_date + timedelta(days=5))

  def test_monthly_workflow_start_date_before_end_date_and_start_date_before_basedate(self):
    from monthdelta import monthdelta
    workflow = self._create_monthly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_month(5), self.day_this_month(10))
    day_15_this_month = self.day_this_month(15)
    day_5_this_month = self.day_this_month(5)
    day_5_next_month = day_5_this_month + monthdelta(1)

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(day_15_this_month)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, day_5_next_month)
    self.assertEqual(end_date, start_date + timedelta(days=5))

  def test_monthly_workflow_start_date_before_end_date_and_start_date_after_basedate(self):
    workflow = self._create_monthly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_month(10), self.day_this_month(15))
    day_5_this_month = self.day_this_month(5)
    day_10_this_month = self.day_this_month(10)
    day_15_this_month = self.day_this_month(15)

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(day_5_this_month)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, day_10_this_month)
    self.assertEqual(end_date, day_15_this_month)

  def test_monthly_workflow_start_date_before_end_date_and_start_date_equals_basedate(self):
    workflow = self._create_monthly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_month(10), self.day_this_month(15))
    day_10_this_month = self.day_this_month(10)
    day_15_this_month = self.day_this_month(15)

    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(day_10_this_month)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, day_10_this_month)
    self.assertEqual(end_date, day_15_this_month)

  def test_monthly_workflow_start_date_after_end_date_and_start_date_after_basedate(self):
    from monthdelta import monthdelta
    workflow = self._create_monthly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_month(15), self.day_this_month(10))
    day_10_this_month = self.day_this_month(10)
    day_10_next_month = day_10_this_month + monthdelta(1)
    day_15_this_month = self.day_this_month(15)
    calc = WorkflowDateCalculator(workflow)
    start_date = calc.nearest_start_date_after_basedate(day_10_this_month)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, day_15_this_month)
    self.assertEqual(end_date, day_10_next_month)

  def test_monthly_workflow_previous_start_date(self):
    oct_21 = self.day_this_year(10, 21)
    dec_8 = self.day_this_year(12, 8)
    workflow = self._create_monthly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_month(4), self.day_this_month(24))
    calculator = WorkflowDateCalculator(workflow)
    start_date = calculator.nearest_start_date_after_basedate(oct_21)
    self.assertEqual(start_date, self.day_this_year(11, 4))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(11, 24))
    previous_cycle_start_date = calculator.previous_cycle_start_date_before_basedate(oct_21)
    self.assertEqual(previous_cycle_start_date, self.day_this_year(10, 4))
    previous_cycle_end_date = calculator.nearest_end_date_after_start_date(previous_cycle_start_date)
    self.assertEqual(previous_cycle_end_date, self.day_this_year(10, 24))


class TestQuarterlyWorkflow(BaseWorkflowDateCalculator):
  def test_quarterly_workflow_calc_start_and_end_date_after_basedate(self):

    jan_4 = self.day_this_year(1, 4)
    feb_3 = self.day_this_year(2, 3)
    mar_2 = self.day_this_year(3, 2)
    apr_4 = self.day_this_year(4, 4)
    may_3 = self.day_this_year(5, 3)
    jun_2 = self.day_this_year(6, 2)
    jul_4 = self.day_this_year(7, 4)
    aug_3 = self.day_this_year(8, 3)
    sep_2 = self.day_this_year(9, 2)
    oct_4 = self.day_this_year(10, 4)
    nov_3 = self.day_this_year(11, 3)
    dec_2 = self.day_this_year(12, 2)

    month_1_workflow = self._create_quarterly_workflow()
    month_1_workflow = self._set_date_range_for_workflow(
      month_1_workflow, self.day_this_year(1,5), self.day_this_year(2,10))
    calc = WorkflowDateCalculator(month_1_workflow)

    start_date = calc.nearest_start_date_after_basedate(jan_4)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(1, 5))
    self.assertEqual(end_date, self.day_this_year(2, 10))

    start_date = calc.nearest_start_date_after_basedate(apr_4)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(4, 5))
    self.assertEqual(end_date, self.day_this_year(5, 10))

    start_date = calc.nearest_start_date_after_basedate(jul_4)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(7, 5))
    self.assertEqual(end_date, self.day_this_year(8, 10))

    start_date = calc.nearest_start_date_after_basedate(oct_4)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(10, 5))
    self.assertEqual(end_date, self.day_this_year(11, 10))

    month_2_workflow = self._create_quarterly_workflow()
    month_2_workflow = self._set_date_range_for_workflow(
      month_2_workflow, self.day_this_year(2,7), self.day_this_year(6,18))
    calc = WorkflowDateCalculator(month_2_workflow)

    start_date = calc.nearest_start_date_after_basedate(feb_3)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(2, 7))
    self.assertEqual(end_date, self.day_this_year(3, 18))

    start_date = calc.nearest_start_date_after_basedate(may_3)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(5, 7))
    self.assertEqual(end_date, self.day_this_year(6, 18))

    start_date = calc.nearest_start_date_after_basedate(aug_3)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(8, 7))
    self.assertEqual(end_date, self.day_this_year(9, 18))

    start_date = calc.nearest_start_date_after_basedate(nov_3)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(11, 7))
    self.assertEqual(end_date, self.day_this_year(12, 18))

    month_3_workflow = self._create_quarterly_workflow()
    month_3_workflow = self._set_date_range_for_workflow(
      month_3_workflow, self.day_this_year(3,7), self.day_this_year(3,18))
    calc = WorkflowDateCalculator(month_3_workflow)

    start_date = calc.nearest_start_date_after_basedate(mar_2)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(3, 7))
    self.assertEqual(end_date, self.day_this_year(3, 18))

    start_date = calc.nearest_start_date_after_basedate(jun_2)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(6, 7))
    self.assertEqual(end_date, self.day_this_year(6, 18))

    start_date = calc.nearest_start_date_after_basedate(sep_2)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(9, 7))
    self.assertEqual(end_date, self.day_this_year(9, 18))

    start_date = calc.nearest_start_date_after_basedate(dec_2)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(12, 7))
    self.assertEqual(end_date, self.day_this_year(12, 18))

  def test_quarterly_workflow_calc_start_date_on_basedate(self):
    month_3_workflow = self._create_quarterly_workflow()
    month_3_workflow = self._set_date_range_for_workflow(
      month_3_workflow, self.day_this_year(3,7), self.day_this_year(3,18))
    calc = WorkflowDateCalculator(month_3_workflow)

    mar_7 = self.day_this_year(3, 7)
    start_date = calc.nearest_start_date_after_basedate(mar_7)
    end_date = calc.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(3, 7))
    self.assertEqual(end_date, self.day_this_year(3, 18))

  def test_quarterly_workflow_calc_start_date_before_basedate(self):
    mar_10 = self.day_this_year(3, 10)
    jan_7  = self.day_this_year(1, 7)
    feb_7  = self.day_this_year(2, 7)
    mar_7  = self.day_this_year(3, 7)
    mar_18 = self.day_this_year(3, 18)

    month_1_workflow = self._create_quarterly_workflow()
    month_1_workflow = self._set_date_range_for_workflow(month_1_workflow, jan_7, mar_18)
    month_2_workflow = self._create_quarterly_workflow()
    month_2_workflow = self._set_date_range_for_workflow(month_2_workflow, feb_7, mar_18)
    month_3_workflow = self._create_quarterly_workflow()
    month_3_workflow = self._set_date_range_for_workflow(month_3_workflow, mar_7, mar_18)

    month_1_calc = WorkflowDateCalculator(month_1_workflow)
    month_2_calc = WorkflowDateCalculator(month_2_workflow)
    month_3_calc = WorkflowDateCalculator(month_3_workflow)

    month_1_start_date = month_1_calc.nearest_start_date_after_basedate(mar_10)
    month_1_end_date = month_1_calc.nearest_end_date_after_start_date(month_1_start_date)
    month_2_start_date = month_2_calc.nearest_start_date_after_basedate(mar_10)
    month_2_end_date = month_2_calc.nearest_end_date_after_start_date(month_2_start_date)
    month_3_start_date = month_3_calc.nearest_start_date_after_basedate(mar_10)
    month_3_end_date = month_3_calc.nearest_end_date_after_start_date(month_3_start_date)

    self.assertEqual(month_1_start_date, self.day_this_year(4, 7))
    self.assertEqual(month_1_end_date, self.day_this_year(6, 18))
    self.assertEqual(month_2_start_date, self.day_this_year(5, 7))
    self.assertEqual(month_2_end_date, self.day_this_year(6, 18))
    self.assertEqual(month_3_start_date, self.day_this_year(6, 7))
    self.assertEqual(month_3_end_date, self.day_this_year(6, 18))

  def test_quarterly_workflow_calc_start_date_after_end_date_and_basedate(self):
    may_9 = self.day_this_year(5, 9)
    workflow_one = self._create_quarterly_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(2,12), self.day_this_year(1,19))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(may_9)
    self.assertEqual(start_date, self.day_this_year(5, 12))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(7, 19))

    workflow_two = self._create_quarterly_workflow()
    workflow_two = self._set_date_range_for_workflow(
      workflow_two, self.day_this_year(2,12), self.day_this_year(2,3))
    calculator = WorkflowDateCalculator(workflow_two)
    start_date = calculator.nearest_start_date_after_basedate(may_9)
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(start_date, self.day_this_year(5, 12))
    self.assertEqual(end_date, self.day_this_year(8, 3))

  def test_quarterly_workflow_wrap_around_year_boundary(self):
    dec_7 = self.day_this_year(12, 7)
    workflow_one = self._create_quarterly_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(3,12), self.day_this_year(1,19))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(dec_7)
    self.assertEqual(start_date, self.day_this_year(12, 12))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    from monthdelta import monthdelta
    self.assertEqual(end_date, self.day_this_year(1, 19) + monthdelta(12))

  def test_quarterly_workflow_start_month_same_start_day_gt_end_day(self):
    feb_3 = self.day_this_year(2, 3)
    workflow_one = self._create_quarterly_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(2,12), self.day_this_year(2,4))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(feb_3)
    self.assertEqual(start_date, self.day_this_year(2, 12))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(5, 4))

    feb_23 = self.day_this_year(2, 23)
    workflow_one = self._create_quarterly_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(2,12), self.day_this_year(2,4))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(feb_23)
    self.assertEqual(start_date, self.day_this_year(5, 12))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(8, 4))

  def test_quarterly_workflow_previous_start_date(self):
    oct_21 = self.day_this_year(10, 21)
    dec_8 = self.day_this_year(12, 8)
    workflow = self._create_quarterly_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_year(1,4), self.day_this_year(2,24))
    calculator = WorkflowDateCalculator(workflow)
    start_date = calculator.nearest_start_date_after_basedate(oct_21)
    self.assertEqual(start_date, self.day_next_year(1, 4))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_next_year(2, 24))
    previous_cycle_start_date = calculator.previous_cycle_start_date_before_basedate(oct_21)
    self.assertEqual(previous_cycle_start_date, self.day_this_year(10, 4))
    previous_cycle_end_date = calculator.nearest_end_date_after_start_date(previous_cycle_start_date)
    self.assertEqual(previous_cycle_end_date, self.day_this_year(11, 24))


class TestAnnualWorkflow(BaseWorkflowDateCalculator):
  def test_annual_start_date_before_end_date_after_basedate(self):
    apr_7 = self.day_this_year(4, 7)
    workflow_one = self._create_annual_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(5,9), self.day_this_year(7,19))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(apr_7)
    self.assertEqual(start_date, self.day_this_year(5, 9))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(7, 19))

  def test_annual_start_date_before_end_date_before_basedate(self):
    jun_7 = self.day_this_year(6, 7)
    workflow_one = self._create_annual_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(5,9), self.day_this_year(7,19))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(jun_7)
    from monthdelta import monthdelta
    self.assertEqual(start_date, self.day_this_year(5, 9) + monthdelta(12))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_this_year(7, 19) + monthdelta(12))

  def test_annual_start_date_after_end_date_after_basedate(self):
    apr_7 = self.day_this_year(4, 7)
    workflow_one = self._create_annual_workflow()
    workflow_one = self._set_date_range_for_workflow(
      workflow_one, self.day_this_year(7,9), self.day_this_year(5,19))
    calculator = WorkflowDateCalculator(workflow_one)
    start_date = calculator.nearest_start_date_after_basedate(apr_7)
    self.assertEqual(start_date, self.day_this_year(7, 9))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    from monthdelta import monthdelta
    self.assertEqual(end_date, self.day_this_year(5, 19) + monthdelta(12))

  def test_annual_workflow_previous_start_date(self):
    dec_8 = self.day_this_year(12, 8)
    workflow = self._create_annual_workflow()
    workflow = self._set_date_range_for_workflow(
      workflow, self.day_this_year(1,4), self.day_this_year(9,24))
    calculator = WorkflowDateCalculator(workflow)
    start_date = calculator.nearest_start_date_after_basedate(dec_8)
    self.assertEqual(start_date, self.day_next_year(1, 4))
    end_date = calculator.nearest_end_date_after_start_date(start_date)
    self.assertEqual(end_date, self.day_next_year(9, 24))
    previous_cycle_start_date = calculator.previous_cycle_start_date_before_basedate(dec_8)
    self.assertEqual(previous_cycle_start_date, self.day_this_year(1, 4))
    previous_cycle_end_date = calculator.nearest_end_date_after_start_date(previous_cycle_start_date)
    self.assertEqual(previous_cycle_end_date, self.day_this_year(9, 24))


class TestRangeLimiting(BaseWorkflowDateCalculator):
  def test_nearest_workday_to_friday_is_friday(self):
    self.assertEqual(self.friday(), WorkflowDateCalculator.adjust_start_date("weekly", self.friday()))
    self.assertEqual(self.friday(), WorkflowDateCalculator.adjust_end_date("weekly", self.friday()))

  def test_nearest_workday_to_monday_is_monday(self):
    self.assertEqual(self.monday(), WorkflowDateCalculator.adjust_start_date("weekly", self.monday()))
    self.assertEqual(self.monday(), WorkflowDateCalculator.adjust_end_date("weekly", self.monday()))

  def test_nearest_start_workday_to_weekend_days_is_monday(self):
    self.assertEqual(self.monday()+timedelta(days=7), WorkflowDateCalculator.adjust_start_date("weekly", self.saturday()))
    self.assertEqual(self.monday()+timedelta(days=7), WorkflowDateCalculator.adjust_start_date("weekly", self.sunday()))

  def test_adjust_start_date_for_one_time(self):
    self.assertEqual(self.saturday(), WorkflowDateCalculator.adjust_start_date("one_time", self.saturday()))
    self.assertEqual(self.sunday(), WorkflowDateCalculator.adjust_start_date("one_time", self.sunday()))

  def test_nearest_end_workday_to_weekend_days_is_friday(self):
    self.assertEqual(self.friday(), WorkflowDateCalculator.adjust_end_date("weekly", self.saturday()))
    self.assertEqual(self.friday(), WorkflowDateCalculator.adjust_end_date("weekly", self.sunday()))

  def test_adjust_end_date_for_one_time(self):
    self.assertEqual(self.saturday(), WorkflowDateCalculator.adjust_end_date("one_time", self.saturday()))
    self.assertEqual(self.sunday(), WorkflowDateCalculator.adjust_end_date("one_time", self.sunday()))

  def test_update_state_on_workflows_without_tasks(self):
    workflows = [
        ("one_time", self._create_one_time_workflow()),
        ("weekly", self._create_weekly_workflow()),
        ("monthly", self._create_monthly_workflow()),
        ("quarterly", self._create_quarterly_workflow()),
        ("annually", self._create_annual_workflow()),
    ]
    for freq, workflow in workflows:
      calculator = WorkflowDateCalculator(workflow)
      next_cycle_start_date = \
          WorkflowDateCalculator.adjust_start_date(freq, calculator.nearest_start_date_after_basedate(self.today()))
      next_cycle_end_date = \
          WorkflowDateCalculator.adjust_end_date(freq, calculator.nearest_end_date_after_start_date(next_cycle_start_date))
      # Check the previous cycle to see if today is mid_cycle.
      previous_cycle_start_date = \
          WorkflowDateCalculator.adjust_start_date(freq, calculator.previous_cycle_start_date_before_basedate(self.today()))
      previous_cycle_end_date = \
          WorkflowDateCalculator.adjust_end_date(freq, calculator.nearest_end_date_after_start_date(previous_cycle_start_date))

if __name__ == '__main__':
  import unittest
  unittest.main()
