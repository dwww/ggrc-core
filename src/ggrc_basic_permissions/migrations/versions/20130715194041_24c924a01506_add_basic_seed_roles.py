# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Add Basic Seed Roles

Revision ID: 24c924a01506
Revises: 3bf5430a8c6f
Create Date: 2013-07-15 19:40:41.254573

"""

# revision identifiers, used by Alembic.
revision = '24c924a01506'
down_revision = '3bf5430a8c6f'

import json
import sqlalchemy as sa
from alembic import op
from datetime import datetime
from sqlalchemy.sql import table, column

roles_table = table('roles',
    column('id', sa.Integer),
    column('name', sa.String),
    column('permissions_json', sa.Text),
    column('description', sa.Text),
    column('modified_by_id', sa.Integer),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime),
    column('context_id', sa.Integer),
    )

def upgrade():
  #create the context 
  program_editor_objects = [
      'Cycle',
      'ObjectDocument',
      'ObjectPerson',
      'Program',
      'ProgramDirective',
      'Relationship',
      ]
  program_owner_objects = list(program_editor_objects)
  program_owner_objects.append('UserRole')

  current_datetime = datetime.now()
  op.bulk_insert(roles_table,
      [
        { 'name': 'ProgramOwner',
          'description': 'User with authorization to peform administrative '\
              'tasks such as associating users to roles within the scope of '\
              'of a program.',
          'permissions_json': json.dumps({
            'create': program_owner_objects,
            'read':   program_owner_objects,
            'update': program_owner_objects,
            'delete': program_owner_objects,
            }),
          'created_at': current_datetime,
          'updated_at': current_datetime,
          'context_id': 1,
        },
        { 'name': 'ProgramEditor',
          'description': 'A user with authorization to edit mapping objects '\
              'related to an access controlled program.',
          'permissions_json': json.dumps({
            'create': program_editor_objects,
            'read':   program_editor_objects,
            'update': program_editor_objects,
            'delete': program_editor_objects,
            }),
          'created_at': current_datetime,
          'updated_at': current_datetime,
          'context_id': 1,
        },
        { 'name': 'ProgramReader',
          'description': 'A user with authorization to read mapping objects '\
              'related to an access controlled program.',
           'permissions_json': json.dumps({
             'create': [],
             'read': program_editor_objects,
             'update': [],
             'delete': [],
             }),
          'created_at': current_datetime,
          'updated_at': current_datetime,
          'context_id': 1,
        },
        { 'name': 'RoleReader',
          'description': 'A user with authorization to read Role resources.',
          'permissions_json': json.dumps({
            'create': [],
            'read':   ['Role',],
            'update': [],
            'delete': [],
            }),
          'created_at': current_datetime,
          'updated_at': current_datetime,
          'context_id': 1,
        },
      ],
      )

  # Eliminate target_context_id to get rid of possible privelege escalation
  # where a user who has role editor priveleges in one context creates
  # similar priveleges for themselves or others in another context
  op.drop_column('users_roles', 'target_context_id')

def downgrade():
  op.execute('SET FOREIGN_KEY_CHECKS = 0')
  op.execute(roles_table.delete().where(
    roles_table.c.name.in_(
      [ op.inline_literal('ProgramOwner'),
        op.inline_literal('ProgramEditor'),
        op.inline_literal('ProgramReader'),
        op.inline_literal('RoleReader'),
      ])))
  op.add_column('users_roles', sa.Column('target_context_id', sa.Integer))
