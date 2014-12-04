# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com

import csv, _csv
import chardet
import os
from ggrc.models import Directive, Section
from StringIO import StringIO
from flask import current_app
from ggrc import db
from .common import ImportException
from ggrc.converters.sections import SectionsConverter
from ggrc.converters.controls import ControlsConverter

def handle_csv_import(converter_class, filepath, **options):
  rows = []
  csv_file = filepath
  if isinstance(filepath, basestring):
    csv_file = open(filepath, 'rbU')

  if options.get('directive_id') and not options.get('directive'):
    options['directive'] = Directive.query.filter_by(id=int(options['directive_id'])).first()

  try:
    if isinstance(csv_file, list):
      rows = [row for row in csv_reader(csv_file)]
    else:
      rows = [row for row in csv_reader(csv_file.read().splitlines(True))]
  except (UnicodeDecodeError, _csv.Error): # Decode error occurs when a special character symbol is inserted in excel.
    raise ImportException("Could not import: invalid character or spreadsheet encountered; verify the file is correctly formatted.")
  if not isinstance(csv_file, list):
    csv_file.close()
  converter = converter_class.from_rows(rows, **options)
  # remove 'dry_run' key to allow passing dict w/out keyword arg collision
  # on 'dry_run' parameter:
  is_dry_run = options.get('dry_run', True)
  del options['dry_run']
  return converter.do_import(is_dry_run, **options)

def csv_reader(csv_data, dialect=csv.excel, **kwargs):
  reader = csv.reader(utf_8_encoder(csv_data), dialect=dialect, **kwargs)
  for row in reader:
    yield [unicode(cell, 'utf-8') for cell in row]

def utf_8_encoder(csv_data):
  """This function is a generator that attempts to encode the string as utf-8.
  It is assumed that the data is likely to be encoded in ascii. If encoding
  fails, however, the function will attempt to guess the encoding and convert
  it to utf-8.

  Guessing is only done when a line fails to encode as there may be characters
  further in the stream that aren't valid ascii and encoding is performed per
  line yielded; guessing is the fallback on a per-line basis.
  """
  for line in csv_data:
    try:
      yield line.decode('utf-8').encode('utf-8')
    except UnicodeDecodeError:
      encoding_guess = chardet.detect(line)['encoding']
      yield line.decode(encoding_guess).encode('utf-8')

def handle_converter_csv_export(filename, objects, converter_class, **options):
  headers = [('Content-Type', 'text/csv'), ('Content-Disposition', 'attachment; filename="{}"'.format(filename))]
  status_code = 200

  exporter = converter_class(objects, **options)
  output_buffer = StringIO()
  writer = csv.writer(output_buffer)

  for metadata_row in exporter.do_export_metadata():
    writer.writerow([ line.encode("utf-8") for line in metadata_row ])

  exporter.do_export(writer)
  body = output_buffer.getvalue()
  output_buffer.close()
  return current_app.make_response((body, 200, headers))

