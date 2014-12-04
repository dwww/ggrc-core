# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Fix nullability in objective related tables

Revision ID: 52362c97efc9
Revises: 16a7fe69e7fd
Create Date: 2013-08-27 12:39:30.134446

"""

# revision identifiers, used by Alembic.
revision = '52362c97efc9'
down_revision = '16a7fe69e7fd'

from alembic import op
import sqlalchemy as sa


NOT_NULL_COLS =     [('section_objectives', 'section_id'),
                     ('section_objectives', 'objective_id'),
                     ('objective_controls', 'objective_id'),
                     ('objective_controls', 'control_id'),
]

EXPLICIT_INDEXES = [('section_objectives', 'section_id', 'sections', 'section_objectives_ibfk_3'),
                    ('section_objectives', 'objective_id', 'objectives', 'section_objectives_ibfk_2'),
                    ('objective_controls', 'objective_id', 'objectives', 'objective_controls_ibfk_3'),
                    ('objective_controls', 'control_id', 'controls', 'objective_controls_ibfk_2'),
]

UNIQUE_CONSTRAINTS = [('section_objectives', ['section_id', 'objective_id']),
                      ('objective_controls', ['objective_id', 'control_id']),
]

def create_explicit_index(table, column, referred_table, constraint_name):
    " Explicit indexes need to be created to work around http://bugs.mysql.com/bug.php?id=21395 "
    op.drop_constraint(constraint_name, table, type_='foreignkey')
    op.create_index('ix_' + column, table, [column])
    op.create_foreign_key(constraint_name, table, referred_table, [column], ['id'])

def drop_explicit_index(table, column, referred_table, constraint_name):
    op.drop_constraint(constraint_name, table, type_='foreignkey')
    op.drop_index('ix_' + column, table)
    op.create_foreign_key(constraint_name, table, referred_table, [column], ['id'])

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

def upgrade():
    op.execute('SET FOREIGN_KEY_CHECKS = 0')
    # Before adding NOT NULL constraint, remove invalid rows.
    for table, column in NOT_NULL_COLS:
        delete_rows_with_null_column(table, column)

    # Before applying UNIQUE constraint, remove duplicate rows.
    for table, columns in UNIQUE_CONSTRAINTS:
        delete_duplicate_rows(table, columns)

    # These FOREIGN KEY constraints existed before, but because we disabled
    #   FOREIGN_KEY_CHECKS, we may have broken constraints.
    for table, column, referred_table, constraint_name in EXPLICIT_INDEXES:
        delete_rows_with_broken_foreign_keys(table, column, referred_table)
    op.execute('SET FOREIGN_KEY_CHECKS = 1')

    for table, column in NOT_NULL_COLS:
        op.alter_column(table, column, nullable=False, existing_type = sa.INTEGER)
    for table, column, referred_table, constraint_name in EXPLICIT_INDEXES:
        create_explicit_index(table, column, referred_table, constraint_name) 
    for table, columns in UNIQUE_CONSTRAINTS:
        op.create_unique_constraint('uq_' + table, table, columns)


def downgrade():
    for table, columns in UNIQUE_CONSTRAINTS:
        op.drop_constraint('uq_' + table, table, type_='unique')
    for table, column, referred_table, constraint_name in EXPLICIT_INDEXES:
        drop_explicit_index(table, column, referred_table, constraint_name) 
    for table, column in NOT_NULL_COLS:
        op.alter_column(table, column, nullable=True, existing_type = sa.INTEGER)
