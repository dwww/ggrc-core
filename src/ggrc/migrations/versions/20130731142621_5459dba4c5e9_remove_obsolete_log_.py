# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Remove obsolete log events table for LogEvents model

Revision ID: 5459dba4c5e9
Revises: 4155c544acb5
Create Date: 2013-07-31 14:26:21.992050

"""

# revision identifiers, used by Alembic.
revision = '5459dba4c5e9'
down_revision = '4155c544acb5'

from alembic import op
import sqlalchemy as sa


def upgrade():
  op.drop_table('log_events')

def downgrade():
  op.create_table('log_events',
  sa.Column('id', sa.Integer(), nullable=False),
  sa.Column('description', sa.Text(), nullable=True),
  sa.Column('severity', sa.String(length=250), nullable=True),
  sa.Column('modified_by_id', sa.String(length=250), nullable=True),
  sa.Column('created_at', sa.DateTime(), nullable=True),
  sa.PrimaryKeyConstraint('id')
  )
