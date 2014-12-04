# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

"""Pre-populate options and categories

Revision ID: 56fa965233f9
Revises: 1b67665113bf
Create Date: 2013-08-13 20:56:45.011928

"""

# revision identifiers, used by Alembic.
revision = '56fa965233f9'
down_revision = '1b67665113bf'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column, select
from sqlalchemy.exc import IntegrityError
import datetime

timestamp = datetime.datetime.now()

options_table = table('options',
    column('id', sa.Integer),
    column('role', sa.String),
    column('title', sa.Text),
    column('description', sa.Text),
    column('modified_by_id', sa.Integer),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime),
    column('required', sa.Boolean),
    column('context_id', sa.Integer),
    )

categories_table = table('categories',
    column('id', sa.Integer),
    column('scope_id', sa.Integer),
    column('name', sa.Text),
    column('parent_id', sa.Integer),
    column('modified_by_id', sa.Integer),
    column('created_at', sa.DateTime),
    column('updated_at', sa.DateTime),
    column('required', sa.Boolean),
    column('context_id', sa.Integer),
    )
options_values = [
      {'role': 'asset_type', 'title': 'Client List', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'asset_type', 'title': 'Employee List', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'asset_type', 'title': 'Ledger Accounts', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'asset_type', 'title': 'Patents', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'asset_type', 'title': 'Personal Identifiable Info', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'asset_type', 'title': 'Source Code', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'asset_type', 'title': 'User Data', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '1 Month', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '1 Week', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '1 Year', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '2 Months', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '2 Weeks', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '3 Months', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '4 Months', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_duration', 'title': '6 Months', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Ad-Hoc', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Annual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Bi-Annual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Continuous', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Daily', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Hourly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Monthly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Quarterly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Semi-Annual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'audit_frequency', 'title': 'Weekly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_kind', 'title': 'Administrative', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_kind', 'title': 'Detective', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_kind', 'title': 'Preventative', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_kind', 'title': 'Reactive', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'Automated', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'Fin - Application', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'Fin - IT-Supported Manual', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'Fin - Manual', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'IT - Automated ITGC', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'IT - IT-Supported ITGC', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'Manual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'control_means', 'title': 'Manual w Segregation of Duties', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'directive_kind', 'title': 'Company Policy', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'directive_kind', 'title': 'Data Asset Policy', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'directive_kind', 'title': 'Operational Group Policy', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'directive_kind', 'title': 'Regulation', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_status', 'title': 'active', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_status', 'title': 'deprecated', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_type', 'title': 'Excel', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_type', 'title': 'PDF', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_type', 'title': 'Text', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_type', 'title': 'URL', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_type', 'title': 'Word', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1980', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1981', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1982', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1983', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1984', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1985', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1986', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1987', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1988', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1989', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1990', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1991', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1992', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1993', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1994', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1995', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1996', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1997', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1998', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '1999', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2000', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2001', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2002', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2003', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2004', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2005', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2006', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2007', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2008', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2009', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2010', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2011', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2012', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'document_year', 'title': '2013', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'entity_kind', 'title': 'Not Applicable', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'entity_type', 'title': 'Business Unit', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'entity_type', 'title': 'Division', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'entity_type', 'title': 'Functional Group', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'entity_type', 'title': 'Legal Entity', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'language', 'title': 'English', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Building', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'HazMat Storage', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Kitchen', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Lab', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Machine Room', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Maintenance Facility', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Office', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Parking Garage', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_kind', 'title': 'Workshop', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Colo Data Center', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Contract Manufacturer', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Data Center', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Distribution Center', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Headquarters', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Regional Office', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Sales Office', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'location_type', 'title': 'Vendor Worksite', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'network_zone', 'title': 'Corp', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'network_zone', 'title': 'Prod', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'person_language', 'title': 'English', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'product_kind', 'title': 'Not Applicable', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'product_type', 'title': 'Appliance', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'product_type', 'title': 'Desktop Software', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'product_type', 'title': 'SaaS', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'reference_type', 'title': 'Database', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'reference_type', 'title': 'Document', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'reference_type', 'title': 'Numeric Data', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'reference_type', 'title': 'Screenshot', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'reference_type', 'title': 'Simple Text', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'reference_type', 'title': 'Website', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'system_kind', 'title': 'Infrastructure', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'system_type', 'title': 'Infrastructure', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'threat_type', 'title': 'Insider Threat', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'threat_type', 'title': 'Outsider Threat', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Ad-Hoc', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Annual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Bi-Annual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Continuous', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Daily', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Hourly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Indeterminate', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Monthly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Quarterly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Semi-Annual', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Transactional', 'required': False, 'created_at': timestamp, 'updated_at': timestamp, },
      {'role': 'verify_frequency', 'title': 'Weekly', 'required': None, 'created_at': timestamp, 'updated_at': timestamp, },
    ]
categories_values = [
      {'name': 'Access Control', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Access Management', 'parent_id': 1, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Authentication', 'parent_id': 1, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Authorization', 'parent_id': 1, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Accuracy', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Application Control', 'parent_id': None, 'scope_id': 100, 'required': False, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Availability', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Business Continuity', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Disaster Recovery', 'parent_id': 8, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Physical Security', 'parent_id': 8, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Change Management', 'parent_id': None, 'scope_id': 100, 'required': False, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Configuration Management', 'parent_id': 11, 'scope_id': 100, 'required': False, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Classification', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Completeness', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Confidentiality', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Confidentiality', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Core', 'parent_id': None, 'scope_id': 101, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Core', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Cutoff', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Environmental', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Existence', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Governance', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Monitoring', 'parent_id': 22, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Policies & Procedures', 'parent_id': 22, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Risk Management', 'parent_id': 22, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Training', 'parent_id': 22, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Integrity', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Occurrence', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Out of Scope', 'parent_id': None, 'scope_id': 101, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Report', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Rights and Obligations', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'SAS70', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Service', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'TBD', 'parent_id': None, 'scope_id': 100, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Understandability', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
      {'name': 'Valuation and Allocation', 'parent_id': None, 'scope_id': 102, 'required': None, 'created_at': timestamp, 'updated_at': timestamp,},
    ]
def upgrade():
    connection = op.get_bind()
    for i, row in enumerate(options_values, start = 1):
      row['id'] = i
      try:
        connection.execute(options_table.insert().values(row))
      except IntegrityError:
        connection.execute(options_table.update().where(options_table.c.id == i).values(row))
    for i, row in enumerate(categories_values, start = 1):
      row['id'] = i
      try:
        connection.execute(categories_table.insert().values(row))
      except IntegrityError:
        connection.execute(categories_table.update().where(categories_table.c.id == i).values(row))
def downgrade():
    pass
