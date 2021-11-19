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

import FreeCAD
import numpy as np


class Plot(object):
    def __init__(self, xray):
        self.plt = None
        try:
            from FreeCAD.Plot import Plot
        except ImportError:
            try:
                from freecad.plot import Plot
            except ImportError:
                FreeCAD.Console.PrintWarning(
                    'Plot module is disabled, so I cannot perform the plot\n')
                return

        self.xray = xray
        self.aspect = (xray.ChamberHeight / xray.ChamberRadius).Value
        self.plt = Plot.figure("Radiography")
        self.plt.update()

    def update(self, img, cmap='gray', vmin=0.0, vmax=1.0):
        self.plt.axes.clear()
        self.plt.axes.imshow(img, cmap=cmap, vmin=vmin, vmax=vmax,
                             aspect=self.aspect)
        self.plt.update()
