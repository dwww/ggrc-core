# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Move system roles to default context.

Revision ID: 33a9ca4c32ac
Revises: 3adc42b4f6b9
Create Date: 2013-10-14 20:36:18.251704

"""

# revision identifiers, used by Alembic.
revision = '33a9ca4c32ac'
down_revision = '3adc42b4f6b9'

import json
import sqlalchemy as sa
from alembic import op
from datetime import datetime
from sqlalchemy.sql import table, column, select

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
  # Move roles into the default context
  op.execute(roles_table.update()\
      .where(
        roles_table.c.name.in_([
          op.inline_literal('ProgramOwner'),
          op.inline_literal('ProgramEditor'),
          op.inline_literal('ProgramReader'),
          op.inline_literal('RoleReader'),
          ]))\
      .values(context_id=None))

  # add Role reading permission to Reader and ProgramOwner roles
  # Reader role assignment will confer Role read in the relevant context,
  # as will ProgramOwner in private program contexts.
  reader_permissions = select(
        [roles_table.c.name, roles_table.c.permissions_json])\
      .where(
        roles_table.c.name.in_([
          op.inline_literal('Reader'),
          op.inline_literal('ProgramOwner'),
          ]))
  connection = op.get_bind()
  reader_permissions = connection.execute(reader_permissions).fetchall()
  for permissions in reader_permissions:
    p = json.loads(permissions['permissions_json'])
    p['read'].append('Role')
    op.execute(roles_table.update()\
        .where(roles_table.c.name == permissions['name'])\
        .values(permissions_json=json.dumps(p)))

def downgrade():
  reader_permissions = select(
        [roles_table.c.name, roles_table.c.permissions_json])\
      .where(
        roles_table.c.name.in_([
          op.inline_literal('Reader'),
          op.inline_literal('ProgramOwner'),
          ]))
  connection = op.get_bind()
  reader_permissions = connection.execute(reader_permissions).fetchall()
  for permissions in reader_permissions:
    p = json.loads(permissions['permissions_json'])
    if 'Role' in p['read']:
      p['read'].remove('Role')
      op.execute(roles_table.update()\
          .where(roles_table.c.name == permissions['name'])\
          .values(permissions_json=json.dumps(p)))

  current_datetime = datetime.now()
  op.execute(roles_table.update()\
      .where(
        roles_table.c.name.in_([
          op.inline_literal('ProgramOwner'),
          op.inline_literal('ProgramEditor'),
          op.inline_literal('ProgramReader'),
          op.inline_literal('RoleReader'),
          ]))\
      .values(context_id=1))
