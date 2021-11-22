#***************************************************************************
#*                                                                         *
#*   Copyright (c) 2015 Jose Luis Cercos Pita <jlcercos@gmail.com>         *
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


__title__="FreeCAD X-Ray module"
__author__ = "Jose Luis Cercos-Pita"
__url__ = "https://gitlab.com/sanguinariojoe/freecad.xray"
__doc__="The X-Rays module provides tools to perform X-Rays simulations"

from .xrayCreate.Tools import createSimulator
from .xrayCreate.Tools import createXRayObject
from .xrayRadiography.Tools import radiography, assemble_radiography
from .xrayRadiography.PlotAux import save_image
