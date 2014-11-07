from flask import Blueprint
from ggrc import settings
from ggrc.app import app

blueprint = Blueprint(
  'gdrive',
  __name__,
  template_folder='templates',
  static_folder='static',
  static_url_path='/static/ggrc_gdrive_integration',
)

import ggrc_gdrive_integration.models

from ggrc import db
from ggrc.models import Program, Audit, Request, Response, \
  DocumentationResponse, InterviewResponse, PopulationSampleResponse, Document, \
  Meeting
from .models.object_folder import Folderable
from .models.object_file import Fileable
from .models.object_event import Eventable
Program.__bases__ = (Folderable,) + Program.__bases__
Program.late_init_folderable()
Audit.__bases__ = (Folderable,) + Audit.__bases__
Audit.late_init_folderable()
Request.__bases__ = (Folderable,) + Request.__bases__
Request.late_init_folderable()
DocumentationResponse.__bases__ = (Folderable,) + DocumentationResponse.__bases__
DocumentationResponse.late_init_folderable()
DocumentationResponse.__bases__ = (Fileable,) + DocumentationResponse.__bases__
DocumentationResponse.late_init_fileable()
# InterviewResponse.__bases__ = (Fileable,) + InterviewResponse.__bases__
# InterviewResponse.late_init_fileable()
PopulationSampleResponse.__bases__ = (Folderable,) + PopulationSampleResponse.__bases__
PopulationSampleResponse.late_init_folderable()
PopulationSampleResponse.__bases__ = (Fileable,) + \
  PopulationSampleResponse.__bases__
PopulationSampleResponse.late_init_fileable()
#Program._publish_attrs.append('object_folders')
Document.__bases__ = (Fileable,) + \
  Document.__bases__
Document.late_init_fileable()
Meeting.__bases__ = (Eventable,) + \
  Meeting.__bases__
Meeting.late_init_eventable()
'''
Some other spitballs from Dan here:

Folderable.extend_class(Program)
class ExtendableMixin(object):
  _publish_attrs = [..]

  def extend_class(cls, target_cls):
    pass

class ProgramWithGDrive(registry.get_model("Program")):
  @declared_attr
  def object_folders(cls):
    pass

ggrc.services.registry["Program"] = ProgramWithGDrive
/api/blah
/api/ggrc_basic_permissions/Program

@Resource.model_get.connect_via(Program)
def augment_program(programs):
  for p in programs:
    p["object_folders"] = 
'''

# Initialize views
import ggrc_gdrive_integration.views

def init_extra_views(app):
  ggrc_gdrive_integration.views.init_extra_views(app)


from ggrc.services.registry import service

contributed_services = [
  service('object_folders', models.ObjectFolder),
  service('object_files', models.ObjectFile),
  service('object_events', models.ObjectEvent)
]

from ggrc_basic_permissions.contributed_roles import RoleContributions

class GDriveRoleContributions(RoleContributions):
  contributions = {
      'Auditor': {
        'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        },
      'ProgramAuditEditor': {
        'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        'create': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        'update': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        'delete': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        },
      'ProgramAuditOwner': {
        'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        'create': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        'update': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        'delete': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        },
      'ProgramAuditReader': {
        'read': ['ObjectFolder', 'ObjectFile', 'ObjectEvent'],
        },
      'ProgramOwner': {
        'read': ['ObjectFolder'],
        'create': ['ObjectFolder'],
        'update': ['ObjectFolder'],
        'delete': ['ObjectFolder'],
        },
      }

ROLE_CONTRIBUTIONS = GDriveRoleContributions()
