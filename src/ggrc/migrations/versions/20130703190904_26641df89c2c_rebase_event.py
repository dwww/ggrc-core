# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Make Event extend Base

Revision ID: 26641df89c2c
Revises: 2a59bef8c738
Create Date: 2013-07-03 19:09:04.246744

"""

# revision identifiers, used by Alembic.
revision = '26641df89c2c'
down_revision = '2a59bef8c738'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('events', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.execute('UPDATE events SET updated_at = created_at')
    op.drop_constraint('events_ibfk_1', 'events', type_='foreignkey')
    op.alter_column('events', 'person_id', existing_type = sa.INTEGER, new_column_name = 'modified_by_id')
    op.create_foreign_key('events_modified_by', 'events', 'people', ['modified_by_id'], ['id'])
    op.add_column('revisions', sa.Column('created_at', sa.DateTime(), nullable=False))
    op.add_column('revisions', sa.Column('updated_at', sa.DateTime(), nullable=False))
    op.add_column('revisions', sa.Column('modified_by_id', sa.INTEGER, nullable=False))
    op.execute('''UPDATE revisions, events SET 
                    revisions.created_at = events.created_at,
                    revisions.updated_at = events.updated_at,
                    revisions.modified_by_id = events.modified_by_id
                WHERE revisions.event_id = events.id''')
    op.create_foreign_key('revisions_modified_by', 'revisions', 'people', ['modified_by_id'], ['id'])


def downgrade():
    op.drop_column('revisions', 'created_at')
    op.drop_column('revisions', 'updated_at')
    op.drop_constraint('revisions_modified_by', 'revisions', type_='foreignkey')
    op.drop_column('revisions', 'modified_by_id')
    op.drop_constraint('events_modified_by', 'events', type_='foreignkey')
    op.alter_column('events', 'modified_by_id', existing_type = sa.INTEGER, new_column_name = 'person_id')
    op.create_foreign_key('events_ibfk_1', 'events', 'people', ['person_id'], ['id'])
    op.drop_column('events', 'updated_at')
