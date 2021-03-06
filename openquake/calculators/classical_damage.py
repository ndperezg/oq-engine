# -*- coding: utf-8 -*-
# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright (C) 2014-2018 GEM Foundation
#
# OpenQuake is free software: you can redistribute it and/or modify it
# under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# OpenQuake is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with OpenQuake. If not, see <http://www.gnu.org/licenses/>.

import numpy

from openquake.baselib.general import AccumDict
from openquake.hazardlib import stats
from openquake.calculators import base, classical_risk


def classical_damage(riskinputs, riskmodel, param, monitor):
    """
    Core function for a classical damage computation.

    :param riskinputs:
        :class:`openquake.risklib.riskinput.RiskInput` objects
    :param riskmodel:
        a :class:`openquake.risklib.riskinput.CompositeRiskModel` instance
    :param param:
        dictionary of extra parameters
    :param monitor:
        :class:`openquake.baselib.performance.Monitor` instance
    :returns:
        a nested dictionary rlz_idx -> asset -> <damage array>
    """
    result = AccumDict(accum=AccumDict())
    for ri in riskinputs:
        for outputs in riskmodel.gen_outputs(ri, monitor):
            for l, out in enumerate(outputs):
                ordinals = [a.ordinal for a in outputs.assets]
                result[l, outputs.rlzi] += dict(zip(ordinals, out))
    return result


@base.calculators.add('classical_damage')
class ClassicalDamageCalculator(classical_risk.ClassicalRiskCalculator):
    """
    Scenario damage calculator
    """
    core_task = classical_damage

    def post_execute(self, result):
        """
        Export the result in CSV format.

        :param result:
            a dictionary (l, r) -> asset_ordinal -> fractions per damage state
        """
        damages_dt = numpy.dtype([(ds, numpy.float32)
                                  for ds in self.riskmodel.damage_states])
        damages = numpy.zeros((self.A, self.R, self.L * self.I), damages_dt)
        for l, r in result:
            for aid, fractions in result[l, r].items():
                damages[aid, r, l] = tuple(fractions)
        stats.set_rlzs_stats(self.datastore, 'damages', damages)
