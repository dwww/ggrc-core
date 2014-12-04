# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Add owner

Revision ID: 1b67665113bf
Revises: 3f7f9669cd45
Create Date: 2013-08-09 21:16:46.926769

"""

# revision identifiers, used by Alembic.
revision = '1b67665113bf'
down_revision = '3f7f9669cd45'

from alembic import op
import sqlalchemy as sa

def upgrade():
    op.add_column('data_assets', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('directives', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('facilities', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('markets', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('objectives', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('org_groups', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('products', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('programs', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('projects', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('risks', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('risky_attributes', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('sections', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.add_column('controls', sa.Column('owner_id', sa.Integer(), nullable=True))


def downgrade():
    op.drop_column('controls', 'owner_id')
    op.drop_column('sections', 'owner_id')
    op.drop_column('risky_attributes', 'owner_id')
    op.drop_column('risks', 'owner_id')
    op.drop_column('projects', 'owner_id')
    op.drop_column('programs', 'owner_id')
    op.drop_column('products', 'owner_id')
    op.drop_column('org_groups', 'owner_id')
    op.drop_column('objectives', 'owner_id')
    op.drop_column('markets', 'owner_id')
    op.drop_column('facilities', 'owner_id')
    op.drop_column('directives', 'owner_id')
    op.drop_column('data_assets', 'owner_id')
