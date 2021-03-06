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

import FreeCADGui as Gui
import FreeCAD as App
import os

class XRayWorkbench(Gui.Workbench):
    """XRay machines simulator"""
    def __init__(self):
        _dir = os.path.dirname(__file__)
        self.__class__.Icon = os.path.join(_dir, "resources", "icons", "XRay_Workbench.svg")
        self.__class__.MenuText = "XRay"
        self.__class__.ToolTip = "XRay module is a simulator of X-Ray machines"

    from . import XRayGui

    def Initialize(self):
        from PySide import QtCore, QtGui

        cmdlist = ["XRay_Create", "XRay_AddObject", "XRay_Radiography",
                   "XRay_CT"]

        self.appendToolbar(
            str(QtCore.QT_TRANSLATE_NOOP("XRay", "XRay")),
            cmdlist)
        self.appendMenu(
            str(QtCore.QT_TRANSLATE_NOOP("XRay", "XRay")),
            cmdlist)

Gui.addWorkbench(XRayWorkbench())
