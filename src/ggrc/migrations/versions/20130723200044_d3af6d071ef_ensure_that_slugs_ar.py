# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Ensure that slugs are unique

Revision ID: d3af6d071ef
Revises: 2b709b655bf
Create Date: 2013-07-23 20:00:44.461976

"""

# revision identifiers, used by Alembic.
revision = 'd3af6d071ef'
down_revision = '2b709b655bf'

from alembic import op
from sqlalchemy.sql import table, column, func
import sqlalchemy as sa

def slugged_table(tablename, singular):
  t = table(tablename,
      column('id', sa.Integer),
      column('slug', sa.String),
      )
  t.singular_name = singular
  return t

slugged_table_names = [
    ('controls', 'Control'),
    ('data_assets', 'Help'),
    ('directives', 'Directive'),
    ('facilities', 'Facility'),
    ('helps', 'Help'),
    ('markets', 'Markets'),
    ('objectives', 'Objective'),
    ('org_groups', 'OrgGroup'),
    ('products', 'Product'),
    ('programs', 'Program'),
    ('projects', 'Project'),
    ('risks', 'Risk'),
    ('risky_attributes', 'RiskyAttribute'),
    ('sections', 'Section'),
    ('systems', 'System'),
    ]

slugged_tables = [slugged_table(*t) for t in slugged_table_names]

def upgrade():
  for t in slugged_tables:
    op.execute(t.update()\
        .where(t.c.slug == '')\
        .values(slug=func.concat(
            op.inline_literal(t.singular_name + " "),
            t.c.id,
            ),
          ))
    op.create_unique_constraint('uq_'+t.name, t.name, ['slug',])

def downgrade():
  for t in slugged_tables:
    op.drop_constraint('uq_'+t.name, t.name, type_='unique')
