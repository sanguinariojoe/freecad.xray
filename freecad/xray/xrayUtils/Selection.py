#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2011, 2016 Jose Luis Cercos Pita <jlcercos@gmail.com>   *
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

import FreeCAD as App
import FreeCADGui as Gui
from FreeCAD import Units
import sys


def __get_shape_solids(obj):
    try:
        return obj.Solids
    except AttributeError:
        try:
            return __get_shape_solids(obj.Shape)
        except AttributeError:
            return []
    return []


def get_solids(objs=None):
    """Returns the selected solids

    Keyword arguments:
    objs -- List of objects to filter. None for Gui.Selection.getSelection()

    Returns:
    The list of objects with solids
    """
    if objs is None:
        objs = Gui.Selection.getSelection()
    filtered = []
    for obj in objs:
        if (__get_shape_solids(obj)):
            filtered.append(obj)
    return filtered


def get_xrays(objs=None):
    """Returns the selected X-Ray machines

    Keyword arguments:
    objs -- List of objects to filter. None for Gui.Selection.getSelection()

    Returns:
    The list of X-Ray machiness
    """
    if objs is None:
        objs = Gui.Selection.getSelection()
    filtered = []
    for obj in objs:
        try:
            if obj.IsXRay:
                filtered.append(obj)
        except AttributeError:
            continue
    return filtered
