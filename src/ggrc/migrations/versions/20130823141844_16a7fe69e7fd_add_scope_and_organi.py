# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Add scope and organization

Revision ID: 16a7fe69e7fd
Revises: 56fa965233f9
Create Date: 2013-08-23 14:18:44.507224

"""

# revision identifiers, used by Alembic.
revision = '16a7fe69e7fd'
down_revision = '56fa965233f9'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column(u'programs', sa.Column('scope', sa.Text(), nullable=True))
    op.add_column(u'programs', sa.Column('organization', sa.String(length=250), nullable=True))


def downgrade():
    op.drop_column(u'programs', 'organization')
    op.drop_column(u'programs', 'scope')
