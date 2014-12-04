# Copyright (C) 2014 Google Inc., authors, and contributors <see AUTHORS file>
# Licensed under http://www.apache.org/licenses/LICENSE-2.0 <see LICENSE file>
# Created By: dan@reciprocitylabs.com
# Maintained By: dan@reciprocitylabs.com


import ggrc.models
from .risk_assessment import RiskAssessment


ggrc.models.all_models.RiskAssessment = RiskAssessment

ggrc.models.all_models.all_models += [
    RiskAssessment,
    ]

ggrc.models.all_models.__all__ += [
    RiskAssessment.__name__,
    ]
