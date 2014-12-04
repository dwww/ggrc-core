# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""ProgramEditor cannot delete program.
Also, update list of all mappings that ProgramEditor can edit.

Revision ID: 5325f2b93af8
Revises: 3909ea856bc9
Create Date: 2013-09-03 12:46:35.653904

"""

# revision identifiers, used by Alembic.
revision = '5325f2b93af8'
down_revision = '3909ea856bc9'

import json
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table, column

roles_table = table('roles',
    column('id', sa.Integer),
    column('name', sa.String),
    column('permissions_json', sa.Text),
    )

original_program_editor_objects = [
      'Cycle',
      'ObjectDocument',
      'ObjectPerson',
      'Program',
      'ProgramDirective',
      'Relationship',
      ]

base_program_editor_objects = [
      'Cycle',
      'ObjectDocument',
      'ObjectPerson',
      'ProgramDirective',
      'Relationship',
      'ObjectObjective',
      'ProgramControl',
      'ObjectSection',
      ]

all_program_editor_objects = list(base_program_editor_objects)
all_program_editor_objects.append('Program')

def upgrade():
  op.execute(roles_table.update()\
      .where(roles_table.c.name == 'ProgramEditor')\
      .values(permissions_json=json.dumps({
            'create': all_program_editor_objects,
            'read':   all_program_editor_objects,
            'update': all_program_editor_objects,
            'delete': base_program_editor_objects,
            })))

def downgrade():
  op.execute(roles_table.update()\
      .where(roles_table.c.name == 'ProgramEditor')\
      .values(permissions_json=json.dumps({
            'create': original_program_editor_objects,
            'read':   original_program_editor_objects,
            'update': original_program_editor_objects,
            'delete': original_program_editor_objects,
            })))
