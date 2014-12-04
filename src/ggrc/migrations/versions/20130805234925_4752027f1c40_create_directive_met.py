# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Create Directive.meta_kind

Revision ID: 4752027f1c40
Revises: 3a5ff1d71b9f
Create Date: 2013-08-05 23:49:25.621647

"""

# revision identifiers, used by Alembic.
revision = '4752027f1c40'
down_revision = '3a5ff1d71b9f'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import select, table, column, and_

def upgrade():
    # Add `directives.meta_kind` to be the subclass discriminator
    op.add_column('directives', sa.Column('meta_kind', sa.String(length=250), nullable=True))

    directives_table = table('directives',
      column('id', sa.Integer),
      column('kind', sa.String),
      column('meta_kind', sa.String)
      )

    meta_kind_mappings = {
        "Contract": ("Contract",),
        "Policy": (
            "Company Policy",
            "Org Group Policy", "Data Asset Policy", "Product Policy",
            "Contract-Related Policy", "Company Controls Policy"
            ),
        "Regulation": ("Regulation",),
        }

    for meta_kind, kinds in meta_kind_mappings.items():
      op.execute(
          directives_table.update()\
              .where(directives_table.c.kind.in_(kinds))\
              .values(meta_kind=meta_kind))

    # We removed 'Controllable' from System/Process, so drop any
    # existing relationships there
    object_controls_table = table('object_controls',
      column('id', sa.Integer),
      column('controllable_type', sa.String),
      column('controllable_id', sa.Integer)
      )

    op.execute(
        object_controls_table.delete()\
            .where(object_controls_table.c.controllable_type.in_(
                ['System', 'Process', 'SystemOrProcess'])))

    # Now, alter mappings to System/Directive to use new class name
    systems_table = table('systems',
      column('id', sa.Integer),
      column('is_biz_process', sa.Boolean)
      )

    directives_table = table('directives',
      column('id', sa.Integer),
      column('meta_kind', sa.Boolean)
      )

    process_ids = select([systems_table.c.id])\
      .where(systems_table.c.is_biz_process == True)
    system_ids = select([systems_table.c.id])\
      .where(systems_table.c.is_biz_process != True)

    contract_ids = select([directives_table.c.id])\
      .where(directives_table.c.meta_kind == 'Contract')
    policy_ids = select([directives_table.c.id])\
      .where(directives_table.c.meta_kind == 'Policy')
    regulation_ids = select([directives_table.c.id])\
      .where(directives_table.c.meta_kind == 'Regulation')

    system_types = ["System", "Process"]
    directive_types = ["Directive", "Contract", "Policy", "Regulation"]

    type_ids_old_types = [
        ("System",     system_ids,     system_types),
        ("Process",    process_ids,    system_types),
        ("Contract",   contract_ids,   directive_types),
        ("Policy",     policy_ids,     directive_types),
        ("Regulation", regulation_ids, directive_types),
        ]

    polymorphic_links = [
        ('object_objectives', 'objectiveable'),
        ('object_controls',   'controllable'),
        ('object_sections',   'sectionable'),
        ('object_people',     'personable'),
        ('object_documents',  'documentable'),
        ('relationships',     'source'),
        ('relationships',     'destination')
        ]

    for table_name, prefix in polymorphic_links:
      t = table(table_name,
        column('id', sa.Integer),
        column('{0}_type'.format(prefix), sa.String),
        column('{0}_id'.format(prefix),   sa.Integer)
        )
      for type, ids, old_types in type_ids_old_types:
        op.execute(t.update()\
            .values(**{ "{0}_type".format(prefix) : type })\
            .where(
              and_(
                t.c.get("{0}_type".format(prefix)).in_(old_types),
                t.c.get("{0}_id".format(prefix)).in_(ids))))


def downgrade():
    op.drop_column('directives', 'meta_kind')
