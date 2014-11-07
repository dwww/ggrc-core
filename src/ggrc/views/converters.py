# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: silas@reciprocitylabs.com
# Maintained By: silas@reciprocitylabs.com

import json

from flask import flash, render_template, request, redirect
from werkzeug.exceptions import Forbidden

from ggrc.app import app
from ggrc.converters.common import ImportException
from ggrc.converters.import_helper import handle_csv_import, handle_converter_csv_export
from ggrc.login import get_current_user, login_required
from ggrc.models.background_task import create_task, queued_task
from ggrc.rbac import permissions
from flask import url_for


_default_context = object()
def ensure_read_permissions_for(resource_type, context_id=_default_context):
  if context_id is _default_context:
    context_id = resource_type.context_id
  if not isinstance(resource_type, basestring):
    if not isinstance(resource_type, type):
      resource_type = resource_type.__class__
    resource_type = resource_type.__name__
  if not permissions.is_allowed_read(resource_type, context_id):
    raise Forbidden()


def ensure_admin_permissions():
  # This is actually wrong, but currently *no one* has permissions for
  # `/admin`, so it works.
  if not permissions.is_allowed_read("/admin", 1):
    raise Forbidden()


def ensure_create_permissions_for(resource_type, context_id):
  if not permissions.is_allowed_create(resource_type, context_id):
    raise Forbidden()


def filter_objects_by_permissions(user, objs):
  from ggrc.rbac.permissions import permissions_for
  permissions = permissions_for(user)

  permitted_objects = []
  for obj in objs:
    if permissions.is_allowed_read(obj.__class__.__name__, obj.context_id):
      permitted_objects.append(obj)
  return permitted_objects


def import_dump(data):
  # The textarea here is a custom response for 'remoteipart' to
  # proxy a JSON response through an iframe.
  return app.make_response((
    '<textarea data-type="application/json" response-code="200">{0}</textarea>'.format(
      json.dumps(data)), 200, [('Content-Type', 'text/html')]))

def import_redirect(location):
  # The textarea here is a custom response for 'remoteipart' to
  # proxy a JSON response through an iframe.
  return app.make_response((
    '<textarea data-type="application/json" response-code="200">{0}</textarea>'.format(
      json.dumps({ 'location': location })), 200, [('Content-Type', 'text/html')]))

def allowed_file(filename):
  return filename.rsplit('.', 1)[1] == 'csv'

ADMIN_KIND_TEMPLATES = {
  "processes": "Process_Import_Template.csv",
  "systems": "System_Import_Template.csv",
  "people": "People_Import_Template.csv",
  "help": "Help_Import_Template.csv",
}

@app.route("/<admin_kind>/import_template", methods=['GET'])
@login_required
def process_import_template(admin_kind):
  from flask import current_app
  ensure_admin_permissions()

  if admin_kind in ADMIN_KIND_TEMPLATES:
    filename = ADMIN_KIND_TEMPLATES[admin_kind]
    headers = [('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename="{}"'.format(filename))]
    body = render_template("csv_files/" + filename)
    return current_app.make_response((body, 200, headers))
  return current_app.make_response((
      "No template for that type.", 404, []))

@app.route("/programs/<program_id>/import_template", methods=['GET'])
@login_required
def system_program_import_template(program_id):
  from flask import current_app
  from ggrc.models import Program
  program = Program.query.get(program_id)
  ensure_read_permissions_for(program)

  if program:
    template_name = "System_Program_Import_Template.csv"
    headers = [('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename="{}"'.format(template_name))]
    options = {"program_slug": program.slug}
    body = render_template("csv_files/" + template_name, **options)
    return current_app.make_response((body, 200, headers))
  return current_app.make_response((
      "No such program.", 404, []))


@app.route("/_background_tasks/import_people", methods=['POST'])
@queued_task
def import_people_task(task):
  from ggrc.converters.people import PeopleConverter
  from ggrc.models import Person

  csv_file = task.parameters.get("csv_file")
  dry_run = task.parameters.get("dry_run")
  try:
    options = {}
    options['dry_run'] = dry_run
    converter = handle_csv_import(PeopleConverter, csv_file.splitlines(True), **options)
    if dry_run:
      options['converter'] = converter
      options['results'] = converter.objects
      options['heading_map'] = converter.object_map
      return render_template("people/import_result.haml", **options)
    else:
      count = len(converter.objects)
      return import_redirect("/admin/people_redirect/{}".format(count))

  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("people/import_result.haml", exception_message=e,
          converter=converter, results=converter.objects, heading_map=converter.object_map)
    return render_template("directives/import_errors.haml",
          directive_id="People", exception_message=str(e))

@app.route("/admin/help_redirect/<count>", methods=["GET"])
def help_redirect(count):
  flash(u'Successfully imported {} help page{}'.format(count, 's' if count > 1 else ''), 'notice alert-success')
  return redirect("/admin")

@app.route("/_background_tasks/import_help", methods=['POST'])
@queued_task
def import_help_task(task):
  from ggrc.converters.help import HelpConverter
  from ggrc.models import Help

  csv_file = task.parameters.get("csv_file")
  dry_run = task.parameters.get("dry_run")
  try:
    options = {}
    options['dry_run'] = dry_run
    converter = handle_csv_import(HelpConverter, csv_file.splitlines(True), **options)
    if dry_run:
      options['converter'] = converter
      options['results'] = converter.objects
      options['heading_map'] = converter.object_map
      return render_template("help/import_result.haml", **options)
    else:
      count = len(converter.objects)
      return import_redirect("/admin/help_redirect/{}".format(count))

  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("help/import_result.haml", exception_message=e,
          converter=converter, results=converter.objects, heading_map=converter.object_map)
    return render_template("directives/import_errors.haml",
          directive_id="Help", exception_message=str(e))

@app.route("/programs/<program_id>/import_controls", methods=['GET', 'POST'])
@login_required
def import_controls_to_program(program_id):
  from ggrc.models import Program
  from werkzeug import secure_filename

  program = Program.query.get(program_id)
  ensure_create_permissions_for("ProgramControl", program.context_id)

  return_to = unicode(request.args.get('return_to') or '')

  if request.method != 'POST':
    return render_template("programs/import_controls.haml", program_id=program_id, import_kind='Controls', return_to=return_to, parent_type="Program")

  if 'cancel' in request.form:
    program_url = request.args.get("return_to") or view_url_for(program)
    return import_redirect(program_url)
  dry_run = not ('confirm' in request.form)
  csv_file = request.files['file']
  if csv_file and allowed_file(csv_file.filename):
    filename = secure_filename(csv_file.filename)
  else:
    file_msg = "Could not import: invalid csv file."
    return render_template("programs/import_errors.haml",
        directive_id=directive_id, exception_message=file_msg)
  parameters = {
      'parent_type': Program,
      'parent_id': int(program_id),
      'dry_run': dry_run,
      'csv_filename': filename,
      'csv_file': csv_file.read(),
      'return_to': return_to,
  }
  tq = create_task(
      "import_control",
      url_for(import_control_program_task.__name__),
      import_control_program_task,
      parameters)
  return tq.make_response(import_dump({"id": tq.id, "status": tq.status}))

@app.route("/standards/<directive_id>/import_objectives", methods=['GET', 'POST'])
@app.route("/regulations/<directive_id>/import_objectives", methods=['GET', 'POST'])
@app.route("/policies/<directive_id>/import_objectives", methods=['GET', 'POST'])
@app.route("/contracts/<directive_id>/import_objectives", methods=['GET', 'POST'])
@login_required
def import_objectives(directive_id):
  from ggrc.models import Directive
  from werkzeug import secure_filename

  directive = Directive.query.get(directive_id)
  ensure_create_permissions_for("ObjectObjective", directive.context_id)
  return_to = unicode(request.args.get('return_to') or '')

  if request.method != 'POST':
    return render_template("directives/import.haml", directive_id=directive_id, import_kind='Objectives', return_to=return_to, parent_type=(directive.kind or directive.meta_kind))

  if 'cancel' in request.form:
    return import_redirect(return_to)
  dry_run = not ('confirm' in request.form)
  csv_file = request.files['file']
  if csv_file and allowed_file(csv_file.filename):
    filename = secure_filename(csv_file.filename)
  else:
    file_msg = "Could not import: invalid csv file."
    return render_template("directives/import_errors.haml",
        directive_id=directive_id, exception_message=file_msg)
  parameters = {
      'parent_type': Directive,
      'parent_id': int(directive_id),
      'dry_run': dry_run,
      'csv_filename': filename,
      'csv_file': csv_file.read(),
      'return_to': return_to,
  }
  tq = create_task(
      "import_objective",
      url_for(import_objective_directive_task.__name__),
      import_objective_directive_task,
      parameters)
  return tq.make_response(import_dump({"id": tq.id, "status": tq.status}))

@app.route("/programs/<program_id>/import_objectives", methods=['GET', 'POST'])
@login_required
def import_objectives_to_program(program_id):
  from ggrc.models import Program
  from werkzeug import secure_filename

  program = Program.query.get(program_id)
  ensure_create_permissions_for("Relationship", program.context_id)
  return_to = unicode(request.args.get('return_to') or '')

  if request.method != 'POST':
    return render_template("programs/import_objectives.haml", program_id=program_id, import_kind='Objectives', return_to=return_to, parent_type="Program")

  if 'cancel' in request.form:
    program_url = request.args.get("return_to") or view_url_for(program)
    return import_redirect(program_url)
  dry_run = not ('confirm' in request.form)
  csv_file = request.files['file']
  if csv_file and allowed_file(csv_file.filename):
    filename = secure_filename(csv_file.filename)
  else:
    file_msg = "Could not import: invalid csv file."
    return render_template("programs/import_errors.haml",
        directive_id=directive_id, exception_message=file_msg)
  parameters = {
      'parent_type': Program,
      'parent_id': int(program_id),
      'dry_run': dry_run,
      'csv_filename': filename,
      'csv_file': csv_file.read(),
      'return_to': return_to,
  }
  tq = create_task(
      "import_objective",
      url_for(import_objective_program_task.__name__),
      import_objective_program_task,
      parameters)
  return tq.make_response(import_dump({"id": tq.id, "status": tq.status}))

@app.route("/_background_tasks/import_objective_directive", methods=['POST'])
@queued_task
def import_objective_directive_task(task):
  from ggrc.converters.objectives import ObjectivesConverter
  from ggrc.models import Directive
  from ggrc.utils import view_url_for

  csv_file = task.parameters.get("csv_file")
  dry_run = task.parameters.get("dry_run")
  directive_id = task.parameters.get("parent_id")
  directive = Directive.query.get(directive_id)
  directive_url = view_url_for(directive)
  return_to = task.parameters.get("return_to") or directive_url

  try:
    converter = handle_csv_import(ObjectivesConverter, csv_file.splitlines(True), **task.parameters)
    if dry_run:
      options = {
          'converter': converter,
          'results': converter.objects,
          'heading_map': converter.object_map,
      }
      return render_template("directives/import_objectives_result.haml", **options)
    else:
      count = len(converter.objects)
      flash(u'Successfully imported {} objective{}'.format(count, 's' if count > 1 else ''), 'notice')
      return import_redirect(return_to)
  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("directives/import_objectives_result.haml",
          exception_message=e, converter=converter, results=converter.objects,
          directive_id=directive_id, heading_map=converter.object_map)
    return render_template("directives/import_errors.haml",
        directive_id=directive_id, exception_message=str(e))

  return render_template("directives/import.haml", directive_id=directive_id, import_kind='Objectives', return_to=return_to, parent_type=(directive.kind or directive.meta_kind))

@app.route("/standards/<directive_id>/import_controls", methods=['GET', 'POST'])
@app.route("/regulations/<directive_id>/import_controls", methods=['GET', 'POST'])
@app.route("/policies/<directive_id>/import_controls", methods=['GET', 'POST'])
@app.route("/contracts/<directive_id>/import_controls", methods=['GET', 'POST'])
@login_required
def import_controls(directive_id):
  from ggrc.models import Directive
  from werkzeug import secure_filename

  directive = Directive.query.get(directive_id)
  ensure_create_permissions_for("DirectiveControl", directive.context_id)

  return_to = unicode(request.args.get('return_to') or '')

  if request.method != 'POST':
    return render_template("directives/import.haml", directive_id=directive_id, import_kind='Controls', return_to=return_to, parent_type=(directive.kind or directive.meta_kind))

  if 'cancel' in request.form:
    return import_redirect(return_to)
  dry_run = not ('confirm' in request.form)
  csv_file = request.files['file']
  if csv_file and allowed_file(csv_file.filename):
    filename = secure_filename(csv_file.filename)
  else:
    file_msg = "Could not import: invalid csv file."
    return render_template("directives/import_errors.haml",
        directive_id=directive_id, exception_message=file_msg)
  parameters = {
      'parent_type': Directive,
      'parent_id': int(directive_id),
      'dry_run': dry_run,
      'csv_filename': filename,
      'csv_file': csv_file.read(),
      'return_to': return_to,
  }
  tq = create_task(
      "import_control",
      url_for(import_control_directive_task.__name__),
      import_control_directive_task,
      parameters)
  return tq.make_response(import_dump({"id": tq.id, "status": tq.status}))

@app.route("/_background_tasks/import_control_directive", methods=['POST'])
@queued_task
def import_control_directive_task(task):
  from ggrc.converters.controls import ControlsConverter
  from ggrc.models import Directive
  from ggrc.utils import view_url_for

  csv_file = task.parameters.get("csv_file")
  dry_run = task.parameters.get("dry_run")
  directive_id = task.parameters.get("parent_id")
  directive = Directive.query.get(directive_id)
  directive_url = view_url_for(directive)
  return_to = task.parameters.get("return_to") or directive_url
  try:
    converter = handle_csv_import(ControlsConverter, csv_file.splitlines(True), **task.parameters)
    if dry_run:
      options = {
          'converter': converter,
          'results': converter.objects,
          'heading_map': converter.object_map,
      }
      return render_template("directives/import_controls_result.haml", **options)
    else:
      count = len(converter.objects)
      flash(u'Successfully imported {} control{}'.format(count, 's' if count > 1 else ''), 'notice')
      return import_redirect(return_to)
  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("directives/import_controls_result.haml",
          exception_message=e, converter=converter, results=converter.objects,
          directive_id=directive_id, heading_map=converter.object_map)
    return render_template("directives/import_errors.haml",
       directive_id=directive_id, exception_message=str(e))

@app.route("/_background_tasks/import_control_program", methods=['POST'])
@queued_task
def import_control_program_task(task):
  from ggrc.converters.controls import ControlsConverter
  from ggrc.models import Program
  from ggrc.utils import view_url_for

  csv_file = task.parameters.get("csv_file")
  dry_run = task.parameters.get("dry_run")
  program_id = task.parameters.get("parent_id")
  program = Program.query.get(program_id)
  program_url = view_url_for(program)
  return_to = task.parameters.get("return_to") or program_url

  try:
    converter = handle_csv_import(ControlsConverter, csv_file.splitlines(True), **task.parameters)
    if dry_run:
      options = {
          'converter': converter,
          'results': converter.objects,
          'heading_map': converter.object_map,
      }
      return render_template("programs/import_controls_result.haml", **options)
    else:
      count = len(converter.objects)
      flash(u'Successfully imported {} control{}'.format(count, 's' if count > 1 else ''), 'notice')
      return import_redirect(return_to)

  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("programs/import_controls_result.haml",
          exception_message=e, converter=converter, results=converter.objects,
          program_id=program.id, heading_map=converter.object_map)
    return render_template("programs/import_errors.haml",
        program_id=program.id, exception_message=str(e))

@app.route("/_background_tasks/import_objective_program", methods=['POST'])
@queued_task
def import_objective_program_task(task):
  from ggrc.converters.objectives import ObjectivesConverter
  from ggrc.models import Program
  from ggrc.utils import view_url_for

  csv_file = task.parameters.get("csv_file")
  dry_run = task.parameters.get("dry_run")
  program_id = task.parameters.get("parent_id")
  program = Program.query.get(program_id)
  program_url = view_url_for(program)
  return_to = task.parameters.get("return_to") or program_url

  try:
    converter = handle_csv_import(ObjectivesConverter, csv_file.splitlines(True), **task.parameters)
    if dry_run:
      options = {
          'converter': converter,
          'results': converter.objects,
          'heading_map': converter.object_map,
      }
      return render_template("programs/import_objectives_result.haml", **options)
    else:
      count = len(converter.objects)
      flash(u'Successfully imported {} objectives{}'.format(count, 's' if count > 1 else ''), 'notice')
      return import_redirect(return_to)

  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("programs/import_objectives_result.haml",
          exception_message=e, converter=converter, results=converter.objects,
          program_id=program.id, heading_map=converter.object_map)
    return render_template("programs/import_errors.haml",
        program_id=program.id, exception_message=str(e))

@app.route("/_background_tasks/import_system", methods=["POST"])
@app.route("/_background_tasks/import_process", methods=["POST"])
@queued_task
def import_system_task(task):
  from ggrc.converters.systems import SystemsConverter

  kind_lookup = {"systems": "System(s)", "processes": "Process(es)"}
  csv_file = task.parameters.get("csv_file")
  object_kind = task.parameters.get("object_kind")
  dry_run = task.parameters.get("dry_run")
  options = {"dry_run": dry_run}
  if object_kind == "processes":
    options["is_biz_process"] = '1'
  try:
    converter = handle_csv_import(SystemsConverter, csv_file.splitlines(True), **options)
    if dry_run:
      return render_template("systems/import_result.haml", converter=converter, results=converter.objects, heading_map=converter.object_map)
    else:
      count = len(converter.objects)
      flash(u'Successfully imported {} {}'.format(count, kind_lookup[object_kind]), 'notice alert-success')
      return import_redirect("/admin")

  except ImportException as e:
    if e.show_preview:
      converter = e.converter
      return render_template("systems/import_result.haml", exception_message=e, converter=converter, results=converter.objects, heading_map=converter.object_map)
    return render_template("directives/import_errors.haml", exception_message=e)

@app.route("/_background_tasks/export_people", methods=['GET'])
@queued_task
def export_people_task(task):
  from ggrc.converters.people import PeopleConverter
  from ggrc.models.all_models import Person
  options = {}
  options['export'] = True
  people = Person.query.all()
  filename = "PEOPLE.csv"
  return handle_converter_csv_export(filename, people, PeopleConverter, **options)

@app.route("/_background_tasks/export_help", methods=['GET'])
@queued_task
def export_help_task(task):
  from ggrc.converters.help import HelpConverter
  from ggrc.models.all_models import Help
  options = {}
  options['export'] = True
  people = Help.query.all()
  filename = "HELP.csv"
  return handle_converter_csv_export(filename, people, HelpConverter, **options)

@app.route("/_background_tasks/export_process", methods=['GET'])
@queued_task
def export_process_task(task):
  from ggrc.converters.systems import SystemsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Process

  options = {}
  options['export'] = True
  options['is_biz_process'] = '1'
  procs = Process.query.all()
  filename = "PROCESSES.csv"
  return handle_converter_csv_export(filename, procs, SystemsConverter, **options)

@app.route("/_background_tasks/export_system", methods=['GET'])
@queued_task
def export_system_task(task):
  from ggrc.converters.systems import SystemsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import System

  options = {}
  options['export'] = True
  systems = System.query.filter_by(is_biz_process=False).all()
  filename = "SYSTEMS.csv"
  return handle_converter_csv_export(filename, systems, SystemsConverter, **options)

@app.route("/admin/people_redirect/<count>", methods=["GET"])
def people_redirect(count):
  flash(u'Successfully imported {} {}'.format(count, 'people' if count > 1 else 'person'), 'notice alert-success')
  return redirect("/admin")

@app.route("/admin/import/<import_type>", methods=['GET', 'POST'])
@login_required
def import_people(import_type):
  import_task = {
    "people": import_people_task,
    "help": import_help_task
  }

  ensure_admin_permissions()

  if request.method != 'POST':
    return render_template(import_type + "/import.haml",
                           import_kind=import_type.capitalize())

  if 'cancel' in request.form:
    return import_redirect("/admin")

  dry_run = not ('confirm' in request.form)
  csv_file = request.files['file']

  if csv_file and allowed_file(csv_file.filename):
    from werkzeug.utils import secure_filename
    filename = secure_filename(csv_file.filename)
  else:
    file_msg = "Could not import: invalid csv file."
    return render_template("directives/import_errors.haml",
        directive_id=import_type.capitalize(), exception_message=file_msg)

  parameters = {"dry_run": dry_run,
                "csv_file": csv_file.read(),
                "csv_filename": filename}
  tq = create_task(
      "import_" + import_type,
      url_for(import_task[import_type].__name__),
      import_task[import_type],
      parameters)
  return tq.make_response(import_dump({"id":tq.id, "status":tq.status}))

@app.route("/audits/<audit_id>/import_pbcs", methods=['GET', 'POST'])
@login_required
def import_requests(audit_id):
  from werkzeug import secure_filename
  from ggrc.converters.common import ImportException
  from ggrc.converters.requests import RequestsConverter
  from ggrc.converters.import_helper import handle_csv_import
  from ggrc.models import Audit, Program
  from ggrc.utils import view_url_for
  from urlparse import urlparse, urlunparse
  import urllib

  audit = Audit.query.get(audit_id)
  program = audit.program
  program_url = view_url_for(program)
  return_to = unicode(request.args.get('return_to', program_url))
  ensure_create_permissions_for("Request", audit.context_id)

  if request.method == 'POST':

    if 'cancel' in request.form:
      return import_redirect(return_to)
    dry_run = not ('confirm' in request.form)
    csv_file = request.files['file']
    try:
      if csv_file and allowed_file(csv_file.filename):
        filename = secure_filename(csv_file.filename)
        converter = handle_csv_import(RequestsConverter, csv_file,
          program_id=program.id, audit_id=audit.id, dry_run=dry_run)

        if dry_run:
          return render_template("programs/import_request_result.haml", converter=converter, results=converter.objects, heading_map=converter.object_map, program_code=program.slug)
        else:
          count = len(converter.objects)
          urlparts = urlparse(request.args.get("return_to"))
          return_to = urlunparse(
            (urlparts.scheme,
              urlparts.netloc,
              u"/audits/post_import_request_hook",
              u'',
              u'return_to=' + urllib.quote_plus(request.args.get("return_to")) \
              + u'&ids=' + json.dumps([object.obj.id for object in converter.objects])
              + u'&audit_id=' + unicode(int(audit_id)),
              '')
          )
          return import_redirect(return_to)

      else:
        file_msg = "Could not import: invalid csv file."
        return render_template("programs/import_request_errors.haml",
              exception_message=file_msg)

    except ImportException as e:
      if e.show_preview:
        converter = e.converter
        return render_template("programs/import_request_result.haml", exception_message=e,
            converter=converter, results=converter.objects,
            heading_map=converter.object_map)
      return render_template("programs/import_request_errors.haml",
            exception_message=e)

  return render_template("programs/import_request.haml", import_kind='Requests', return_to=return_to)

@app.route("/audits/post_import_request_hook", methods=['GET'])
def post_import_requests():
  return import_redirect(request.args.get("return_to"))

@app.route("/audits/<audit_id>/import_pbc_template", methods=['GET'])
@login_required
def import_requests_template(audit_id):
  from flask import current_app
  from ggrc.models.all_models import Audit, Program
  audit = Audit.query.get(audit_id)
  ensure_read_permissions_for(audit)
  program = audit.program
  template = "Request_Import_Template.csv"
  filename = "PBC Request Import Template.csv"
  headers = [('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename="{}"'.format(filename))]
  options = {'program_slug': program.slug}
  body = render_template("csv_files/" + template, **options)
  return current_app.make_response((body, 200, headers))

@app.route("/standards/<directive_id>/import_sections", methods=['GET', 'POST'])
@app.route("/regulations/<directive_id>/import_sections", methods=['GET', 'POST'])
@app.route("/policies/<directive_id>/import_sections", methods=['GET', 'POST'])
@app.route("/contracts/<directive_id>/import_clauses", methods=['GET', 'POST'])
@login_required
def import_sections(directive_id):
  from werkzeug import secure_filename
  from ggrc.converters.common import ImportException
  from ggrc.converters.sections import SectionsConverter, ClausesConverter
  from ggrc.converters.import_helper import handle_csv_import
  from ggrc.models import Directive, Contract
  from ggrc.utils import view_url_for

  directive = Directive.query.get(directive_id)
  directive_url = view_url_for(directive)
  return_to = unicode(request.args.get('return_to', directive_url))
  # TODO: Further separate clause vs section import handler when it's
  # possible to import clauses to non-Contracts, sections to Contracts
  # For now, just decide import type based on directive type
  import_kind = "Sections"
  object_converter = SectionsConverter
  if isinstance(directive, Contract):
    import_kind = "Clauses"
    object_converter = ClausesConverter
    ensure_create_permissions_for("Clause", directive.context_id)
  else:
    ensure_create_permissions_for("Section", directive.context_id)

  if request.method == 'POST':

    if 'cancel' in request.form:
      return import_redirect(return_to)
    csv_file = request.files['file']
    dry_run = not ('confirm' in request.form)
    options = {
        "dry_run": dry_run,
        "directive_id": directive_id,
        "import_kind": import_kind[:-1],  # strip off plural
    }
    try:
      if csv_file and allowed_file(csv_file.filename):
        filename = secure_filename(csv_file.filename)
        converter = handle_csv_import(object_converter, csv_file, **options)
        if dry_run:
          return render_template("directives/import_sections_result.haml",
              directive_id=directive_id, converter=converter,
              results=converter.objects, heading_map=converter.object_map)
        else:
          count = len(converter.objects)
          flash(u'Successfully imported {0} {2}{1}'.format(
              count, 's' if count > 1 else '', import_kind[:-1]), 'notice')
          return import_redirect(return_to)
      else:
        file_msg = "Could not import: invalid csv file."
        return render_template("directives/import_errors.haml",
              directive_id=directive_id, exception_message=file_msg)

    except ImportException as e:
      if e.show_preview:
        converter = e.converter
        return render_template("directives/import_sections_result.haml", exception_message=e,
            converter=converter, results=converter.objects,
            directive_id=int(directive_id), heading_map=converter.object_map)
      return render_template("directives/import_errors.haml",
            directive_id=int(directive_id), exception_message=e)

  return render_template(
      "directives/import.haml", directive_id=directive_id, import_kind=import_kind, return_to=return_to)

@app.route("/<object_kind>/import", methods=['GET', 'POST'])
@login_required
def import_systems_processes(object_kind):
  if not permissions.is_allowed_read("/admin", 1):
    raise Forbidden()
  kind_lookup = {"systems": "Systems", "processes": "Processes"}
  if object_kind == "systems":
    ensure_create_permissions_for("System", None)
  elif object_kind == "processes":
    ensure_create_permissions_for("Process", None)
  else:
    raise Forbidden()

  if object_kind in kind_lookup:
    import_kind = kind_lookup[object_kind]
  else:
    return current_app.make_response((
        "Invalid import type.", 404, []))
  if request.method != 'POST':
    return render_template("systems/import.haml", import_kind=import_kind)

  if 'cancel' in request.form:
    return import_redirect('/admin')
  dry_run = not ('confirm' in request.form)
  csv_file = request.files['file']
  if csv_file and allowed_file(csv_file.filename):
    from werkzeug import secure_filename
    filename = secure_filename(csv_file.filename)
  else:
    file_msg = "Could not import: invalid csv file."
    return render_template("directives/import_errors.haml", exception_message=file_msg)
  parameters = {"dry_run": dry_run, "csv_file": csv_file.read(), "csv_filename": filename, "object_kind": object_kind}
  tq = create_task(
      "import_system",
      url_for(import_system_task.__name__),
      import_system_task,
      parameters)
  return tq.make_response(import_dump({"id": tq.id, "status": tq.status}))

@app.route("/programs/<program_id>/import_systems", methods=['GET', 'POST'])
@login_required
def import_systems_to_program(program_id):
  from werkzeug import secure_filename
  from ggrc.converters.common import ImportException
  from ggrc.converters.systems import SystemsConverter
  from ggrc.converters.import_helper import handle_csv_import
  from ggrc.models import Program
  from ggrc.utils import view_url_for

  program = Program.query.get(program_id)
  ensure_create_permissions_for("Relationship", program.context_id)

  program_url = view_url_for(program)
  return_to = unicode(request.args.get('return_to', program_url))

  if request.method == 'POST':
    if 'cancel' in request.form:
      return import_redirect(return_to)
    dry_run = not ('confirm' in request.form)
    csv_file = request.files['file']
    try:
      if csv_file and allowed_file(csv_file.filename):
        filename = secure_filename(csv_file.filename)
        options = {
            "dry_run": dry_run,
            "parent_type": Program,
            "parent_id": program_id,
        }
        converter = handle_csv_import(SystemsConverter, csv_file, **options)
        if dry_run:
          return render_template("systems/import_result.haml",
            converter=converter, results=converter.objects, heading_map=converter.object_map)
        else:
          count = len(converter.objects)
          flash(
              u'Successfully imported {0} system{1} to {2}'.format(
                  count,
                  's' if count > 1 else '',
                  program.display_name
              ),
              'notice'
          )
          return import_redirect(return_to)
      else:
        file_msg = "Could not import: invalid csv file."
        return render_template("directives/import_errors.haml", exception_message=file_msg)

    except ImportException as e:
      if e.show_preview:
        converter = e.converter
        return render_template("systems/import_result.haml", exception_message=e,
            converter=converter, results=converter.objects, heading_map=converter.object_map)
      return render_template("directives/import_errors.haml", exception_message=e)

  return render_template("systems/import.haml", import_kind='Systems')

@app.route("/admin/export/<export_type>", methods=['GET'])
@login_required
def export(export_type):
  ensure_admin_permissions()

  export_task = {
    "people": export_people_task,
    "help": export_help_task,
    "process": export_process_task,
    "system": export_system_task,
  }

  tq = create_task(
      "export_" + export_type,
      url_for(export_task[export_type].__name__),
      export_task[export_type])
  return import_dump({"id":tq.id, "status":tq.status})

@app.route("/standards/<directive_id>/export_sections", methods=['GET'])
@app.route("/regulations/<directive_id>/export_sections", methods=['GET'])
@app.route("/policies/<directive_id>/export_sections", methods=['GET'])
@login_required
def export_sections(directive_id):
  from ggrc.converters.sections import SectionsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Directive

  options = {}
  directive = Directive.query.filter_by(id=int(directive_id)).first()
  ensure_read_permissions_for(directive)
  options['directive'] = directive
  options['export'] = True
  filename = "{}.csv".format(directive.slug)
  sections = directive.sections
  return handle_converter_csv_export(filename, sections, SectionsConverter, **options)

@app.route("/contracts/<directive_id>/export_clauses", methods=['GET'])
@login_required
def export_clauses(directive_id):
  from ggrc.converters.sections import SectionsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Directive

  options = {}
  directive = Directive.query.filter_by(id=int(directive_id)).first()
  ensure_read_permissions_for(directive)
  options['directive'] = directive
  options['export'] = True
  filename = "{}.csv".format(directive.slug)
  sections = directive.joined_sections
  return handle_converter_csv_export(filename, sections, SectionsConverter, **options)

@app.route("/standards/<directive_id>/export_objectives", methods=['GET'])
@app.route("/regulations/<directive_id>/export_objectives", methods=['GET'])
@app.route("/policies/<directive_id>/export_objectives", methods=['GET'])
@app.route("/contracts/<directive_id>/export_objectives", methods=['GET'])
@login_required
def export_objectives(directive_id):
  from ggrc.converters.objectives import ObjectivesConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Directive, Objective

  directive = Directive.query.get(directive_id)
  ensure_read_permissions_for(directive)
  options = {
      'parent_type': directive.__class__,
      'parent_id': directive_id,
      'export': True,
  }
  filename = "{}-objectives.csv".format(directive.slug)
  if 'ids' in request.args:
    ids = request.args['ids'].split(",")
    objectives = Objective.query.filter(Objective.id.in_(ids))
  else:
    objectives = directive.objectives
  return handle_converter_csv_export(filename, objectives, ObjectivesConverter, **options)

@app.route("/programs/<program_id>/export_objectives", methods=['GET'])
@login_required
def export_objectives_from_program(program_id):
  from ggrc.converters.objectives import ObjectivesConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Program, Objective

  program = Program.query.filter_by(id=int(program_id)).first()
  ensure_read_permissions_for(program)
  ensure_read_permissions_for("Relationship", program.context_id)
  options = {
      'export': True,
      'parent_type': Program,
      'parent_id': program_id,
  }
  filename = "{}-objectives.csv".format(program.slug)
  if 'ids' in request.args:
    ids = request.args['ids'].split(",")
    objectives = Objective.query.filter(Objective.id.in_(ids))
  else:
    objectives = program.objectives
  return handle_converter_csv_export(filename, objectives, ObjectivesConverter, **options)

@app.route("/standards/<directive_id>/import_sections_template", methods=['GET'])
@app.route("/regulations/<directive_id>/import_sections_template", methods=['GET'])
@app.route("/policies/<directive_id>/import_sections_template", methods=['GET'])
@app.route("/contracts/<directive_id>/import_clauses_template", methods=['GET'])
@login_required
def import_directive_sections_template(directive_id):
  from flask import current_app
  from ggrc.models.all_models import Directive
  directive = Directive.query.filter_by(id=int(directive_id)).first()
  ensure_read_permissions_for(directive)
  directive_type = directive.type
  DIRECTIVE_TYPES = ['Contract', 'Regulation', 'Standard', 'Policy']
  if directive_type not in DIRECTIVE_TYPES:
    return current_app.make_response((
        "No template for that type.", 404, []))
  if directive_type == "Contract":
    section_term = "Clause"
  else:
    section_term = "Section"
  output_filename = "{0}_{1}_Import_Template.csv".format(
      directive_type, section_term)
  headers = [('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename="{}"'.format(output_filename))]
  options = {
    'section_term': section_term,
    'directive_type': directive_type,
    'directive_slug': directive.slug,
  }
  body = render_template("csv_files/Section_Import_Template.csv", **options)
  return current_app.make_response((body, 200, headers))

@app.route("/audits/<audit_id>/export_pbcs", methods=['GET'])
@login_required
def export_requests(audit_id):
  from ggrc.converters.requests import RequestsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Audit, Request

  options = {}
  audit = Audit.query.get(audit_id)
  ensure_read_permissions_for(audit)
  program = audit.program
  options['program_id'] = program.id
  filename = "{}-requests.csv".format(program.slug)
  if 'ids' in request.args:
    ids = request.args['ids'].split(",")
    requests = Request.query.filter(Request.id.in_(ids))
  else:
    requests = audit.requests
  options['export'] = True
  return handle_converter_csv_export(filename, requests, RequestsConverter, **options)

@app.route("/standards/<directive_id>/export_controls", methods=['GET'])
@app.route("/regulations/<directive_id>/export_controls", methods=['GET'])
@app.route("/policies/<directive_id>/export_controls", methods=['GET'])
@app.route("/contracts/<directive_id>/export_controls", methods=['GET'])
@login_required
def export_controls(directive_id):
  from ggrc.converters.controls import ControlsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Directive, Control

  directive = Directive.query.filter_by(id=int(directive_id)).first()
  ensure_read_permissions_for(directive)

  options = {
      'export': True,
      'parent_type': directive.__class__,
      'parent_id': directive_id,
  }
  filename = "{}-controls.csv".format(directive.slug)
  if 'ids' in request.args:
    ids = request.args['ids'].split(",")
    controls = Control.query.filter(Control.id.in_(ids))
  else:
    controls = directive.controls
  filter_objects_by_permissions(get_current_user(), controls)
  return handle_converter_csv_export(filename, controls, ControlsConverter, **options)


@app.route("/programs/<program_id>/export_controls", methods=['GET'])
@login_required
def export_controls_from_program(program_id):
  from ggrc.converters.controls import ControlsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Program, Control

  program = Program.query.filter_by(id=int(program_id)).first()
  ensure_read_permissions_for(program)
  ensure_read_permissions_for("ProgramControl", program.context_id)

  options = {
      'export': True,
      'parent_type': Program,
      'parent_id': program_id,
  }
  filename = "{}-controls.csv".format(program.slug)
  if 'ids' in request.args:
    ids = request.args['ids'].split(",")
    controls = Control.query.filter(Control.id.in_(ids))
  else:
    controls = program.controls
  return handle_converter_csv_export(filename, controls, ControlsConverter, **options)

@app.route("/programs/<program_id>/export_systems", methods=['GET'])
@login_required
def export_systems_from_program(program_id):
  from ggrc.converters.systems import SystemsConverter
  from ggrc.converters.import_helper import handle_converter_csv_export
  from ggrc.models.all_models import Program, System

  program = Program.query.get(program_id)
  ensure_read_permissions_for(program)
  ensure_read_permissions_for("Relationship", program.context_id)

  options = {
      'export': True,
      'parent_type': Program,
      'parent_id': program_id
  }
  filename = "{}-systems.csv".format(program.slug)
  if 'ids' in request.args:
    ids = request.args['ids'].split(",")
    systems = System.query.filter(System.id.in_(ids))
  else:
    # if no id list given, look up from which relationships of this
    # program have a System as destination
    systems = [r.System_destination for r in program.related_destinations if r.System_destination]
  return handle_converter_csv_export(filename, systems, SystemsConverter, **options)

@app.route("/<object_type>/<object_id>/import_objectives_template", methods=['GET'])
@app.route("/<object_type>/<object_id>/import_controls_template", methods=['GET'])
@login_required
def import_controls_template(object_type, object_id):
  from flask import current_app
  from ggrc.models.all_models import Directive, Program
  # mapping from template/import type to formatted type name
  IMPORT_TYPE_MAP = {
      "import_objectives_template": "Objective",
      "import_controls_template": "Control",
  }
  end_of_path = request.path.split("/")[-1]
  import_type = IMPORT_TYPE_MAP[end_of_path]
  DIRECTIVE_TYPES = ["regulations", "contracts", "policies", "standards"]
  OTHER_TYPES = ["programs"]
  if object_type in DIRECTIVE_TYPES + OTHER_TYPES:
    if object_type in DIRECTIVE_TYPES:
      parent_object = Directive.query.get(object_id)
      parent_kind = parent_object.meta_kind
    else:
      parent_object = Program.query.get(object_id)
      parent_kind = "Program"
    ensure_read_permissions_for(parent_object)
  else:
    return current_app.make_response(
        ("No template for that type.", 404, []))
  template_name = "{}_Import_Template.csv".format(import_type)
  headers = [
      ('Content-Type', 'text/csv'),
      (
          'Content-Disposition',
          'attachment; filename="{0}_{1}"'.format(
              parent_kind,
              template_name
          )
      )
  ]
  options = {
    # (Policy/Regulation/Contract) Code
    'object_kind': parent_kind,
    'object_slug': parent_object.slug,
  }
  body = render_template("csv_files/" + template_name, **options)
  return current_app.make_response((body, 200, headers))
