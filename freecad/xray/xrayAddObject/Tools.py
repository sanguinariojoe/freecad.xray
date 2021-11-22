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
from .. import ObjectInstance


__COMPOUNDS = []
__ELEMENTS = []


def phys_properties_folder():
    _dir = os.path.dirname(__file__)
    return os.path.join(_dir, "..", "resources", "phys_properties")


def parse_presets_file(fname):
    presets = []
    with open(os.path.join(phys_properties_folder(), fname), 'r') as f:
        lines = f.readlines()
        for line in lines[1:]:
            if line.strip() == "":
                continue
            fields = line.strip().split(',')
            while len(fields) > 2:
                fields = [fields[0] + ',' + fields[1]] + fields[2:]
            presets.append([fields[0][1:-1], float(fields[1])])
    return presets


def init_presets(combo_box):
    combo_box.clear()
    global __COMPOUNDS, __ELEMENTS
    __COMPOUNDS = parse_presets_file("compounds.csv")
    for name, dens in __COMPOUNDS:
        combo_box.addItem(name)
    __ELEMENTS = parse_presets_file("elements.csv")
    for name, dens in __ELEMENTS:
        combo_box.addItem(name)


def get_preset(i):
    if i >= len(__COMPOUNDS):
        return __ELEMENTS[i - len(__COMPOUNDS)][:]
    return __COMPOUNDS[i][:]


def get_preset_index(name):
    for i, elem in enumerate(__COMPOUNDS):
        if elem[0] == name:
            return i
    for i, elem in enumerate(__ELEMENTS):
        if elem[0] == name:
            return i + len(__COMPOUNDS)
    return None


def load_preset(i):
    _, dens = get_preset(i)
    dens = Units.parseQuantity('{} g/cm^3'.format(dens))
    z = i + 1
    fformat = "c{:02d}.csv"
    if i >= len(__COMPOUNDS):
        z -= len(__COMPOUNDS)
        fformat = "z{:02d}.csv"
    data = []
    fname = os.path.join(phys_properties_folder(), fformat.format(z))
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


def createXRayObject(parent, source, dens, freqs, attenuations):
    obj = App.ActiveDocument.addObject("Part::FeaturePython", "XRay")
    xray = ObjectInstance.XRayObj(obj, source, dens, freqs, attenuations)
    ObjectInstance.ViewProviderXRayObj(obj.ViewObject)
    App.ActiveDocument.recompute()

    # Add it to the XRay machine
    objs = parent.ScanObjects[:]
    objs.append(obj)
    parent.ScanObjects = objs

    return obj
