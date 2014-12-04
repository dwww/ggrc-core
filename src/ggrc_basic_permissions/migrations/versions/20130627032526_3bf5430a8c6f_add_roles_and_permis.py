# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: david@reciprocitylabs.com
# Maintained By: david@reciprocitylabs.com

"""Add roles and permissions tables

Revision ID: 3bf5430a8c6f
Revises: None
Create Date: 2013-06-27 03:25:26.571232

"""

# revision identifiers, used by Alembic.
revision = '3bf5430a8c6f'
down_revision = None

from alembic import op
import sqlalchemy as sa

def upgrade():
  op.create_table('roles',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('name', sa.String(length=128), nullable=False),
    sa.Column('permissions_json', sa.Text(), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column(
      'created_at', sa.DateTime(), default=sa.text('current_timestamp')),
    sa.Column(
      'updated_at',
      sa.DateTime(),
      default=sa.text('current_timestamp'),
      onupdate=sa.text('current_timestamp')),
    sa.Column('context_id', sa.Integer()),
    )
  op.create_table('users_roles',
    sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
    sa.Column('role_id', sa.Integer(), nullable=False),
    sa.Column('user_email', sa.String(length=128), nullable=False),
    sa.Column('target_context_id', sa.Integer(), nullable=False),
    sa.Column('modified_by_id', sa.Integer()),
    sa.Column(
      'created_at', sa.DateTime(), default=sa.text('current_timestamp')),
    sa.Column(
      'updated_at',
      sa.DateTime(),
      default=sa.text('current_timestamp'),
      onupdate=sa.text('current_timestamp')),
    sa.Column('context_id', sa.Integer()),
    sa.ForeignKeyConstraint(['role_id',], ['roles.id',]),
    )

def downgrade():
  op.drop_table('users_roles')
  op.drop_table('roles')

