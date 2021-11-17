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


import os
import sys
import math
import FreeCAD as App
from FreeCAD import Units
from .. import Instance


__ELEMENTS = []


def phys_properties_folder():
    _dir = os.path.dirname(__file__)
    return os.path.join(_dir, "..", "resources", "phys_properties")


def init_presets(combo_box):
    global __ELEMENTS
    combo_box.clear()
    with open(os.path.join(phys_properties_folder(), "elements.csv"), 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            fields = line.strip().split(',')
            while len(fields) > 3:
                fields = [fields[0] + ',' + fields[1]] + fields[2:]
            name, z, dens = fields[0][1:-1], int(fields[1]), float(fields[2])
            __ELEMENTS.append([name, z, dens])
            combo_box.addItem(name)


def get_preset(i):
    return __ELEMENTS[i][:]


def get_preset_index(name):
    for i, elem in enumerate(__ELEMENTS):
        if elem[0] == name:
            return i
    return None


def load_preset(i):
    dens = Units.parseQuantity('{} g/cm^3'.format(__ELEMENTS[i][2]))
    z = __ELEMENTS[i][1]
    data = []
    fname = os.path.join(phys_properties_folder(), "z{:02d}.csv".format(z))
    with open(fname, 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            fields = [float(field) for field in line.strip().split(',')]
            e = Units.parseQuantity('{} MeV'.format(fields[0]))
            if len(data) > 0 and e == data[-1][0]:
                e = 1.01 * e
            mu = Units.parseQuantity('{} cm^2/g'.format(fields[1]))
            data.append([e, mu])
    return dens, data
