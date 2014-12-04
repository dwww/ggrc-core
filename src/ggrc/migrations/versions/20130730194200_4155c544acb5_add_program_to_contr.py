# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Add program to control mappings

Revision ID: 4155c544acb5
Revises: 2bf7c04016c9
Create Date: 2013-07-22 22:54:08.000779

"""

# revision identifiers, used by Alembic.
revision = '4155c544acb5'
down_revision = '2bf7c04016c9'

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.create_table('program_controls',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column(
      'created_at', sa.DateTime(), default=sa.text('current_timestamp')),
    sa.Column(
      'updated_at',
      sa.DateTime(),
      default=sa.text('current_timestamp'),
      onupdate=sa.text('current_timestamp')),
    sa.Column('context_id', sa.Integer(), default=None),
    sa.Column('program_id', sa.Integer()),
    sa.Column('control_id', sa.Integer()),
    )
  op.create_foreign_key(
      'fk_program_controls_program',
      'program_controls',
      'programs',
      ['program_id'],
      ['id'],
      )
  op.create_foreign_key(
      'fk_program_controls_control',
      'program_controls',
      'controls',
      ['control_id'],
      ['id'],
      )

def downgrade():
  op.drop_constraint(
      'fk_program_controls_program', 'program_controls', type_='foreignkey')
  op.drop_constraint(
      'fk_program_controls_control', 'program_controls', type_='foreignkey')
  op.drop_table('program_controls')
