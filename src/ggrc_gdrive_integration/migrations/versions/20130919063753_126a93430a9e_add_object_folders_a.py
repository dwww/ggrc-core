# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: brad@reciprocitylabs.com
# Maintained By: brad@reciprocitylabs.com
"""add object_folders and object_files

Revision ID: 126a93430a9e
Revises: None
Create Date: 2013-09-19 06:37:53.530926

"""

# revision identifiers, used by Alembic.
revision = '126a93430a9e'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade():

  op.create_table('object_folders',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('permissions_json', sa.Text(), nullable=False),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column(
      'created_at', sa.DateTime(), default=sa.text('current_timestamp')),
    sa.Column(
      'updated_at',
      sa.DateTime(),
      default=sa.text('current_timestamp'),
      onupdate=sa.text('current_timestamp')),
    sa.Column('context_id', sa.Integer()),
    sa.Column('parent_folder_id', sa.String(length=250), nullable=True),
    sa.Column('folder_id', sa.String(length=250), nullable=False),
    sa.Column('folderable_id', sa.Integer(), nullable=False),
    sa.Column('folderable_type', sa.String(length=250), nullable=False),
    )

  op.create_table('object_files',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('permissions_json', sa.Text(), nullable=False),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column(
      'created_at', sa.DateTime(), default=sa.text('current_timestamp')),
    sa.Column(
      'updated_at',
      sa.DateTime(),
      default=sa.text('current_timestamp'),
      onupdate=sa.text('current_timestamp')),
    sa.Column('context_id', sa.Integer()),
    sa.Column('parent_folder_id', sa.String(length=250), nullable=True),
    sa.Column('file_id', sa.String(length=250), nullable=False),
    sa.Column('fileable_id', sa.Integer(), nullable=False),
    sa.Column('fileable_type', sa.String(length=250), nullable=False),
    )

def downgrade():
  op.drop_table('object_folders')
  op.drop_table('object_files')
