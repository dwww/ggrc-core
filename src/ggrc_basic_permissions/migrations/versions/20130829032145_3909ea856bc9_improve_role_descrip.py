# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Improve role descriptions.

Revision ID: 3909ea856bc9
Revises: 5a2eeba0b192
Create Date: 2013-08-29 03:21:45.339649

"""

# revision identifiers, used by Alembic.
revision = '3909ea856bc9'
from sqlalchemy.sql import table, column
down_revision = '5a2eeba0b192'

from alembic import op
import sqlalchemy as sa

roles_table = table('roles',
    column('name', sa.String),
    column('description', sa.Text),
    )

def upgrade():
    op.execute(roles_table.update()\
        .where(roles_table.c.name == 'ProgramOwner')\
        .values(description=\
          'User with authorization to peform administrative tasks such as '
          'associating users to roles within the scope of of a program.<br/>'
          '<br/>'
          'When a person creates a program they are automatically given the '
          'ProgramOwner role. This allows them to Edit, Delete, or Map objects '
          'to the Program. It also allows them to add people and assign them '
          'roles when their programs are private. ProgramOwner is the most '
          'powerful role.'))
    op.execute(roles_table.update()\
        .where(roles_table.c.name == 'ProgramEditor')\
        .values(description=\
          'A user with authorization to edit mapping objects related to an '
          'access controlled program.<br/>'
          '<br/>'
          'When a person has this role they can map and unmap objects to the '
          'Program but they are unable to edit the Program info, delete the '
          'Program, or assign other people roles for that program.'))
    op.execute(roles_table.update()\
        .where(roles_table.c.name == 'ProgramReader')\
        .values(description=\
          'A user with authorization to read mapping objects related to an '
          'access controlled Program.<br/>'
          '<br/>'
          'This is essentially a view only role. A person with this role can '
          'access and view an otherwise private program, but they cannot map '
          'to or edit that program in any way.'))

def downgrade():
    op.execute(roles_table.update()\
        .where(roles_table.c.name == 'ProgramOwner')\
        .values(description=\
          'User with authorization to peform administrative tasks such as '
          'associating users to roles within the scope of of a program.'))
    op.execute(roles_table.update()\
        .where(roles_table.c.name == 'ProgramEditor')\
        .values(description=\
          'A user with authorization to edit mapping objects related to an '
          'access controlled program.'))
    op.execute(roles_table.update()\
        .where(roles_table.c.name == 'ProgramReader')\
        .values(description=\
          'A user with authorization to read mapping objects related to an '
          'access controlled program.'))
