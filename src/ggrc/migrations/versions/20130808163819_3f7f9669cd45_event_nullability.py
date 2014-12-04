# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""event_nullability

Revision ID: 3f7f9669cd45
Revises: 4752027f1c40
Create Date: 2013-08-08 16:38:19.523418

"""

# revision identifiers, used by Alembic.
revision = '3f7f9669cd45'
down_revision = '4752027f1c40'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('events', 'http_method',
        new_column_name='action',
        type_ = sa.Enum(u'POST', u'PUT', u'DELETE', u'IMPORT'),
        existing_type = sa.Enum(u'POST', u'PUT', u'DELETE'),
        nullable = False
    )
    op.alter_column('events', 'resource_id',
        existing_type = sa.Integer(),
        nullable = True
    )
    op.alter_column('events', 'resource_type',
        existing_type=sa.VARCHAR(length=250),
        nullable = True
    )

def downgrade():
    op.alter_column('events', 'resource_type',
        existing_type=sa.VARCHAR(length=250),
        nullable = False
    )
    op.alter_column('events', 'resource_id',
        existing_type = sa.Integer(),
        nullable = False
    )
    op.alter_column('events', 'action',
        new_column_name='http_method',
        type_ = sa.Enum(u'POST', u'PUT', u'DELETE'),
        existing_type = sa.Enum(u'POST', u'PUT', u'DELETE', u'IMPORT'),
        nullable = False
    )
