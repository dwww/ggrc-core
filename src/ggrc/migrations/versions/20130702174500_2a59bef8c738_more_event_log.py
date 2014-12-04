# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Event log support

Revision ID: 2a59bef8c738
Revises: f36bd5f6b5d
Create Date: 2013-06-28 22:52:46.373691

"""

# revision identifiers, used by Alembic.
revision = '2a59bef8c738'
down_revision = 'f36bd5f6b5d'
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

def upgrade():
    op.alter_column('revisions', u'content',
               existing_type=sa.TEXT,
               nullable=False)
    op.alter_column('events', 'http_method',
        type_ = sa.Enum(u'POST', u'PUT', u'DELETE'),
        existing_type = sa.VARCHAR(length=250),
        nullable = False
    )
    op.add_column('events', sa.Column('context_id', sa.Integer(), nullable=True))
    op.add_column('revisions', sa.Column('context_id', sa.Integer(), nullable=True))

def downgrade():
    op.drop_column('revisions', 'context_id')
    op.drop_column('events', 'context_id')
    op.alter_column('events', 'http_method',
        type_ = sa.VARCHAR(length=250),
        existing_type = sa.Enum(u'POST', u'PUT', u'DELETE'),
        nullable = False
    )
    op.alter_column('revisions', u'content',
               existing_type=sa.VARCHAR(length=250),
               nullable=False)
