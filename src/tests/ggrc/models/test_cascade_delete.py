# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: vraj@reciprocitylabs.com
# Maintained By: vraj@reciprocitylabs.com

from ggrc import db
from ggrc.models import ProgramDirective
from tests.ggrc import TestCase
from .factories import ProgramFactory, DirectiveFactory

class TestCascadeDelete(TestCase):
  def test_cascade_delete(self):
    program = ProgramFactory()
    directive = DirectiveFactory()
    program.directives.append(directive)
    db.session.commit()
    program_directives = db.session.query(ProgramDirective).one()
    self.assertEqual(program, program_directives.program) 
    db.session.delete(program)
    db.session.commit()
    self.assertEqual(0, db.session.query(ProgramDirective).count(), 'Delete of Program should delete its ProgramDirectives')
