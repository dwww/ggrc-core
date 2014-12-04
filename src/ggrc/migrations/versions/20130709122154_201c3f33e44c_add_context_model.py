# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Add context model

Revision ID: 201c3f33e44c
Revises: 26641df89c2c
Create Date: 2013-07-09 12:21:54.312795

"""

# revision identifiers, used by Alembic.
revision = '201c3f33e44c'
down_revision = '26641df89c2c'

from alembic import op
from sqlalchemy.sql import table, column
import sqlalchemy as sa

all_tables = [
    'categorizations',
    'categories',
    'controls',
    'control_assessments',
    'control_controls',
    'control_risks',
    'control_sections',
    'cycles',
    'data_assets',
    'directives',
    'documents',
    'facilities',
    'helps',
    'markets',
    'meetings',
    'object_documents',
    'object_people',
    'options',
    'org_groups',
    'pbc_lists',
    'people',
    'population_samples',
    'products',
    'programs',
    'program_directives',
    'projects',
    'relationships',
    'relationship_types',
    'requests',
    'responses',
    'risks',
    'risk_risky_attributes',
    'risky_attributes',
    'sections',
    'systems',
    'system_controls',
    'system_systems',
    'transactions',
    'revisions',
    'events',
    ]

def upgrade():
  op.create_table('contexts',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('related_object_id', sa.Integer(), nullable=True),
    sa.Column('related_object_type', sa.String(length=128), nullable=True),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column(
      'created_at', sa.DateTime(), default=sa.text('current_timestamp')),
    sa.Column(
      'updated_at',
      sa.DateTime(),
      default=sa.text('current_timestamp'),
      onupdate=sa.text('current_timestamp')),
    sa.Column('context_id', sa.Integer(), default=None),
    )
  contexts_table = table('contexts',
      column('id', sa.Integer),
      column('name', sa.String),
      column('description', sa.Text),
      column('related_object_id', sa.Integer),
      column('related_object_type', sa.String),
      column('modified_by_id', sa.Integer),
      column('created_at', sa.DateTime),
      column('updated_at', sa.DateTime),
      column('context_id', sa.Integer),
      )
  op.execute(contexts_table.insert().values(
      name = 'Administration',
      description = 'Context for Administrative resources.',
      modified_by_id = 0,
      context_id = 1,
      ))
  for t in all_tables:
    op.execute(
      'UPDATE {table_name} SET context_id = NULL'.format(table_name=t))
    op.create_foreign_key(
        'fk_{0}_contexts'.format(t),
        t,
        'contexts',
        ['context_id'],
        ['id'],
        )

def downgrade():
  for table in all_tables:
    op.drop_constraint(
        'fk_{0}_contexts'.format(table), table, type_='foreignkey')
  op.drop_table('contexts')

