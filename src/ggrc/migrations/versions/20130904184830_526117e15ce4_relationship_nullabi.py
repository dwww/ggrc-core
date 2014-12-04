# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Relationship nullability

Revision ID: 526117e15ce4
Revises: 52362c97efc9
Create Date: 2013-09-04 18:48:30.727457

"""

# revision identifiers, used by Alembic.
revision = '526117e15ce4'
down_revision = '52362c97efc9'

from alembic import op
import sqlalchemy as sa


NOT_NULL_COLS =     [('relationships', 'source_id', sa.INTEGER),
                     ('relationships', 'source_type', sa.String(length=250)),
                     ('relationships', 'destination_id', sa.INTEGER),
                     ('relationships', 'destination_type', sa.String(length=250)),
                     ('object_controls', 'controllable_id', sa.INTEGER),
                     ('object_controls', 'controllable_type', sa.String(length=250)),
                     ('object_documents', 'documentable_id', sa.INTEGER),
                     ('object_documents', 'documentable_type', sa.String(length=250)),
                     ('object_objectives', 'objectiveable_id', sa.INTEGER),
                     ('object_objectives', 'objectiveable_type', sa.String(length=250)),
                     ('object_people', 'personable_id', sa.INTEGER),
                     ('object_people', 'personable_type', sa.String(length=250)),
                     ('object_sections', 'sectionable_id', sa.INTEGER),
                     ('object_sections', 'sectionable_type', sa.String(length=250)),
                     ('program_controls', 'program_id', sa.INTEGER),
                     ('program_controls', 'control_id', sa.INTEGER),
]

UNIQUE_CONSTRAINTS = [('relationships', ['source_id', 'source_type', 'destination_id', 'destination_type']),
                      ('object_controls', ['control_id', 'controllable_id', 'controllable_type']),
                      ('object_documents', ['document_id', 'documentable_id', 'documentable_type']),
                      ('object_objectives', ['objective_id', 'objectiveable_id', 'objectiveable_type']),
                      ('object_people', ['person_id', 'personable_id', 'personable_type']),
                      ('object_sections', ['section_id', 'sectionable_id', 'sectionable_type']),
                      ('program_controls', ['program_id', 'control_id']),
]

EXPLICIT_INDEXES = [('object_controls', 'control_id', 'controls', 'object_controls_ibfk_2'),
                    ('object_documents', 'document_id', 'documents', 'object_documents_ibfk_1'),
                    ('object_objectives', 'objective_id', 'objectives', 'object_objectives_ibfk_2'),
                    ('object_people', 'person_id', 'people', 'object_people_ibfk_1'),
                    ('object_sections', 'section_id', 'sections', 'object_sections_ibfk_2'),
                    ('program_controls', 'program_id', 'programs', 'fk_program_controls_program'),
                    ('program_controls', 'control_id', 'controls', 'fk_program_controls_control'),
]

def delete_duplicate_rows(table, columns):
    """Find duplicate rows based on `columns`, and remove all but the first
    """
    sql_template = '''
      DELETE t1.* FROM {table} AS t1
        INNER JOIN
          (SELECT id, {comma_columns} FROM {table}
            GROUP BY {comma_columns} HAVING COUNT(*) > 1)
          AS t2
          ON ({join_condition})
        WHERE t1.id != t2.id
    '''
    comma_columns = ", ".join(columns)
    join_condition=" AND ".join(
        ['t1.{column} = t2.{column}'.format(column=c) for c in columns])
    op.execute(sql_template.format(
        table=table, comma_columns=comma_columns, join_condition=join_condition))

def delete_rows_with_null_column(table, column):
    op.execute(
        'DELETE FROM {table} WHERE {column} IS NULL'.format(
            table=table, column=column))

def delete_rows_with_broken_foreign_keys(table, column, referred_table):
    """
    Remove rows with failing foreign key relationships
    * assumes the `referred_table` column is `id`

    Note: This is not sufficient if the `referred_table` is also the `table`
      of another foreign key, but that isn't the case in this migration.
    """
    op.execute(
        'DELETE FROM {table} WHERE {column} NOT IN (SELECT id FROM {referred_table})'.format(
            table=table, column=column, referred_table=referred_table))

def create_explicit_index(table, column, referred_table, constraint_name):
    " Explicit indexes need to be created to work around http://bugs.mysql.com/bug.php?id=21395 "
    op.drop_constraint(constraint_name, table, type_='foreignkey')
    op.create_index('ix_' + column, table, [column])
    op.create_foreign_key(constraint_name, table, referred_table, [column], ['id'])

def drop_explicit_index(table, column, referred_table, constraint_name):
    op.drop_constraint(constraint_name, table, type_='foreignkey')
    op.drop_index('ix_' + column, table)
    op.create_foreign_key(constraint_name, table, referred_table, [column], ['id'])

def upgrade():
    op.execute('SET FOREIGN_KEY_CHECKS = 0')
    # Before adding NOT NULL constraint, remove invalid rows.
    for table, column, existing_type in NOT_NULL_COLS:
        delete_rows_with_null_column(table, column)

    # Before applying UNIQUE constraint, remove duplicate rows.
    for table, columns in UNIQUE_CONSTRAINTS:
        delete_duplicate_rows(table, columns)

    # These FOREIGN KEY constraints existed before, but because we disabled
    #   FOREIGN_KEY_CHECKS, we may have broken constraints.
    for table, column, referred_table, constraint_name in EXPLICIT_INDEXES:
        delete_rows_with_broken_foreign_keys(table, column, referred_table)
    op.execute('SET FOREIGN_KEY_CHECKS = 1')

    for table, column, existing_type in NOT_NULL_COLS:
        op.alter_column(table, column, nullable=False, existing_type = existing_type)
    for table, column, referred_table, constraint_name in EXPLICIT_INDEXES:
        create_explicit_index(table, column, referred_table, constraint_name) 
    for table, columns in UNIQUE_CONSTRAINTS:
        op.create_unique_constraint('uq_' + table, table, columns)

    op.create_table('directive_controls',
      sa.Column('id', sa.Integer(), nullable=False),
      sa.Column('modified_by_id', sa.Integer(), nullable=True),
      sa.Column('created_at', sa.DateTime(), nullable=True),
      sa.Column('updated_at', sa.DateTime(), nullable=True),
      sa.Column('directive_id', sa.Integer(), nullable=False),
      sa.Column('control_id', sa.Integer(), nullable=False),
      sa.Column('context_id', sa.Integer(), nullable=True),
      sa.PrimaryKeyConstraint('id')
    )
    for column, referred_table in [('directive_id', 'directives'), ('control_id', 'controls'), ('context_id', 'contexts')]:
      op.create_index('ix_' + column, 'directive_controls', [column])
      op.create_foreign_key('fk_' + column, 'directive_controls', referred_table, [column], ['id'])
    op.create_unique_constraint('uq_directive_controls', 'directive_controls', ['directive_id', 'control_id'])


def downgrade():
    for table, columns in UNIQUE_CONSTRAINTS:
        op.drop_constraint('uq_' + table, table, type_='unique')
    for table, column, referred_table, constraint_name in EXPLICIT_INDEXES:
        drop_explicit_index(table, column, referred_table, constraint_name) 
    for table, column, existing_type in NOT_NULL_COLS:
        op.alter_column(table, column, nullable=True, existing_type = existing_type)
    op.drop_table('directive_controls')
