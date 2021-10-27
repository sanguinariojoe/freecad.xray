#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2021 Jose Luis Cercos Pita <jlcercos@gmail.com>         *
#*                                                                         *
#*   This program is free software; you can redistribute it and/or modify  *
#*   it under the terms of the GNU Lesser General Public License (LGPL)    *
#*   as published by the Free Software Foundation; either version 2 of     *
#*   the License, or (at your option) any later version.                   *
#*   for detail see the LICENCE text file.                                 *
#*                                                                         *
#*   This program is distributed in the hope that it will be useful,       *
#*   but WITHOUT ANY WARRANTY; without even the implied warranty of        *
#*   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the         *
#*   GNU Library General Public License for more details.                  *
#*                                                                         *
#*   You should have received a copy of the GNU Library General Public     *
#*   License along with this program; if not, write to the Free Software   *
#*   Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  *
#*   USA                                                                   *
#*                                                                         *
#***************************************************************************


import sys
import math
import FreeCAD as App
from .. import Instance


PRESETS = [
    {'name':'Medical shoft X-Rays',
     'min':App.Units.parseQuantity('1 keV'),
     'max':App.Units.parseQuantity('10 keV'),
     'mu':App.Units.parseQuantity('6 keV')},
    {'name':'Crystallography',
     'min':App.Units.parseQuantity('5 keV'),
     'max':App.Units.parseQuantity('16 keV'),
     'mu':App.Units.parseQuantity('10 keV')},
    {'name':'Medical hard X-Rays',
     'min':App.Units.parseQuantity('1 keV'),
     'max':App.Units.parseQuantity('110 keV'),
     'mu':App.Units.parseQuantity('70 keV')},
    {'name':'Airport security',
     'min':App.Units.parseQuantity('50 keV'),
     'max':App.Units.parseQuantity('300 keV'),
     'mu':App.Units.parseQuantity('200 keV')},
    {'name':'Metallography',
     'min':App.Units.parseQuantity('250 keV'),
     'max':App.Units.parseQuantity('350 keV'),
     'mu':App.Units.parseQuantity('300 keV')},
]


def skewed_gauss(mu, sigma=5, alpha=0, n=20):
    min_val = sys.float_info.max
    max_val = 0.0
    vals = []
    for x in range(n):
        xx = (x - mu) / (math.sqrt(2) * sigma)
        vals.append(math.exp(-xx**2) * (1.0 + math.erf(alpha * xx)))
        min_val = min(min_val, vals[-1])
        max_val = max(max_val, vals[-1])
    return [(v - min_val) / (max_val - min_val) for v in vals]


def ligth_preset(i, n=20):
    preset = PRESETS[i]

    # Get the skew and sigma
    de = preset['max'] - preset['min']
    dmu = preset['mu'] - preset['min']
    f = (dmu / de).Value
    sigma = n / 2 * min(f, 1 - f)
    alpha = -5 * (f - 0.5)

    return preset['min'], preset['max'], skewed_gauss(f * n, sigma, alpha, n)


def createSimulator(min_energy, max_energy, spectrum, samples, emitter_type,
                    radius, height, distance, res_x, res_y):
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "XRay")
    xray = Instance.XRay(obj, min_energy, max_energy, spectrum, samples,
                         emitter_type, radius, height, distance, res_x, res_y)
    Instance.ViewProviderXRay(obj.ViewObject)
    App.ActiveDocument.recompute()
    return obj
